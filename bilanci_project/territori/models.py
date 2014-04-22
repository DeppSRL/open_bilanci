# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from model_utils import Choices
from django.contrib.gis.db import models
from datetime import datetime
import struct

class TerritoriManager(models.GeoManager):

    def nazione(self):
        return Territorio.objects.get(territorio= Territorio.TERRITORIO.N )

    def regioni(self, with_nation=False):
        codes = [ Territorio.TERRITORIO.R ]
        if with_nation:
            codes.append( Territorio.TERRITORIO.N )
            codes.append( Territorio.TERRITORIO.E )
        return self.get_query_set().filter(territorio__in= codes )

    def provincie(self):
        return self.get_query_set().filter(territorio= Territorio.TERRITORIO.P )

    def province(self):
        return self.provincie()

    def comuni(self):
        return self.get_query_set().filter(territorio= Territorio.TERRITORIO.C )

    def get_from_istat_code(self, istat_code):
        """
        get single record from Territorio, starting from ISTAT code
        ISTAT code has the form RRRPPPCCC, where
         - RRR is the regional code, zero padded
         - PPP is the provincial code, zero padded
         - CCC is the municipal code, zero padded

        if a record in Territorio is not found, then the ObjectDoesNotExist exception is thrown
        """
        if istat_code is None:
            return None

        if len(istat_code) != 9:
            return None

        (cod_reg, cod_prov, cod_com) = struct.unpack('3s3s3s', istat_code)
        return self.get_query_set().get(cod_reg=int(cod_reg), cod_prov=int(cod_prov), cod_com=str(int(cod_prov))+cod_com)

class Territorio(models.Model):
    TERRITORIO = Choices(
        (u'C', u'Comune'),
        (u'P', u'Provincia'),
        (u'R', u'Regione'),
        (u'N', u'Nazionale'),
        (u'E', u'Estero'),
        (u'L', u'Cluster'),
        )

    CLUSTER = Choices(
        (u'1',u"i_piu_piccoli", u'I più piccoli'),
        (u'2', u"molto_piccoli", u'Molto piccoli'),
        (u'3', u"piccoli_1", u'Piccoli 1'),
        (u'4', u"piccoli_2", u'Piccoli 2'),
        (u'5', u"medio_piccoli", u'Medio piccoli'),
        (u'6', u"medi", u'Medi'),
        (u'7', u"grandi", u'Grandi'),
        (u'8', u"molto_grandi", u'Molto grandi'),
        (u'9', u"i_piu_grandi", u'I più grandi'),
        )

    # codice sito Finanza Locale
    cod_finloc = models.CharField(max_length=128, blank=True, null=True, db_index=True, unique=True)

    # codice Openpolis
    op_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)

    # codice Istat
    istat_id = models.CharField(max_length=20, blank=True, null=True, db_index=True)

    prov = models.CharField(max_length=2, blank=True, null=True)
    regione = models.CharField(max_length=32, blank=True, null=True)
    denominazione = models.CharField(max_length=128, db_index=True)
    slug = models.SlugField(max_length=256, null=True, blank=True)
    territorio = models.CharField(max_length=1, choices=TERRITORIO, db_index=True)
    geom = models.MultiPolygonField(srid=4326, null=True, blank=True)
    cluster = models.CharField(max_length=1, choices=CLUSTER, db_index=True)
    objects = TerritoriManager()


    @property
    def codice(self):
        if self.territorio == u'C':
            return self.cod_com
        elif self.territorio == u'P':
            return self.cod_prov
        else:
            return self.cod_reg

    def get_hierarchy(self):
        """
        returns the list of parent objects (me included)
        """
        if self.territorio == self.TERRITORIO.R:
            return [self]
        elif self.territorio == self.TERRITORIO.P:
            regione = Territorio.objects.regioni().get(cod_reg=self.cod_reg)
            return [regione, self]
        elif self.territorio == self.TERRITORIO.C:
            regione = Territorio.objects.regioni().get(cod_reg=self.cod_reg)
            provincia = Territorio.objects.provincie().get(cod_prov=self.cod_prov)
            return [regione, provincia, self]
        elif self.territorio == self.TERRITORIO.N:
            return [self]

    def get_breadcrumbs(self):
        return [(t.denominazione, t.get_absolute_url()) for t in self.get_hierarchy()]

    @property
    def nome(self):
        return u"%s" % self.denominazione


    @property
    def nome_con_provincia(self):
        if self.territorio == self.TERRITORIO.P:
            return u"{0} (Provincia)".format(self.nome)
        else:
            return u"{0} ({1})".format(self.nome,self.prov)


    def get_abitanti(self, anno=settings.TERRITORI_CONTEXT_REFERENCE_YEAR):
        try:
            contesto = self.contesto_set.get(anno=anno)
            return contesto.bil_popolazione_residente
        except ObjectDoesNotExist:
            return None


    def latest_contesto(self, anno = None):
        contesto = None
        if self.territorio == Territorio.TERRITORIO.C:
            if anno:
                try:
                    contesto = self.contesto_set.filter(anno__lte=anno).order_by('-anno')[0]
                except (AttributeError, IndexError):
                    return None

            else:
                try:
                    contesto = self.contesto_set.all().order_by('-anno')[0]
                except (AttributeError, IndexError):
                    return None

        return contesto

    def best_bilancio_type(self, year):
        """
        Return consuntivo, as first choice, if available,
        else preventivo, as second choice-

        Return None if nothing's available (no-data).
        """
        available_types = self.valorebilancio_set.all().values_list('voce__slug', flat=True).filter(
            anno=year, voce__slug__in=('preventivo-entrate', 'consuntivo-entrate'))

        if 'consuntivo-entrate' in available_types:
            return 'consuntivo'
        elif 'preventivo-entrate' in available_types:
            return 'preventivo'
        else:
            raise Exception()

    def nearest_valid_population(self, year):
        """
        Fetch resident population data from context.
        If the current year's context has no valid population,
        the previous year is considered, then the next,
        then 2/3 years before, then 2/3 after.
        If no valid result is found, None is returned

        :param year: year of start for the search

        :return: a tuple of 2 elements (year, population)
        """
        if self.territorio == Territorio.TERRITORIO.C:
            valid_pops = dict(
                self.contesto_set.filter(bil_popolazione_residente__isnull=False).\
                    values_list('anno', 'bil_popolazione_residente')
            )
            if year in valid_pops:
                return (year, valid_pops[year])
            else:
                for i in range(1, 4):
                    if (year - i) in valid_pops:
                        return (year-1, valid_pops[year - i])
                    elif (year + i) in valid_pops:
                        return (year+1, valid_pops[year + i])

                return None
        else:
            return None

    def __unicode__(self):
        return unicode(self.denominazione)




    class Meta:
        verbose_name = u'Località'
        verbose_name_plural = u'Località'
        ordering = ['denominazione']


class Contesto(models.Model):
    anno = models.PositiveSmallIntegerField(null=False, default=0)
    territorio = models.ForeignKey(Territorio, null=False, default=0)
    bil_nuclei_familiari = models.IntegerField(null=True, default=None, blank=True)
    bil_superficie_urbana = models.IntegerField(null=True, default=None, blank=True)
    bil_superficie_totale = models.IntegerField(null=True, default=None, blank=True)
    bil_strade_esterne = models.IntegerField(null=True, default=None, blank=True)
    bil_strade_interne = models.IntegerField(null=True, default=None, blank=True)
    bil_strade_montane = models.IntegerField(null=True, default=None, blank=True)

    ##
    # NOTE: bil_popolazione_residente is the actual field, the data in istat_abitanti is unused
    ##

    bil_popolazione_residente = models.IntegerField(null=True, default=None, blank=True)

    # Istat context data
    istat_abitanti = models.IntegerField(null=True, default=None, blank=True)
    istat_maschi = models.IntegerField(null=True, default=None, blank=True)
    istat_femmine = models.IntegerField(null=True, default=None, blank=True)

    @staticmethod
    def get_context(anno_str, territorio):
        """
        get territorio context record from Territorio, starting from year
        if a record for the chosen year is not found, the previous year is taken
        """
        anno = int(anno_str)
        comune_context = None

        while comune_context is None and anno >= settings.START_YEAR:
            try:
                comune_context = Contesto.objects.get(
                    anno = int(anno),
                    territorio = territorio,
                )
            except ObjectDoesNotExist:
                anno -= 1

        return comune_context




    def __unicode__(self):
        return u"{0} ({1})".format(self.territorio, self.anno)

    class Meta:
        verbose_name = u'Contesto'
        verbose_name_plural = u'Contesti'
        ordering = ['territorio']



class Incarico(models.Model):

    ##
    # Caches the Incarico data from Open Politici API for each Territorio
    ##

    TIPOLOGIA = Choices(
        (u'1',u"sindaco", u'Sindaco'),
        (u'2', u"commissario", u'Commissario'),
        (u'3', u"vicesindaco_ff", u'Vicesindaco f.f.'),
        )

    territorio = models.ForeignKey(Territorio, null=False, default=0)

    data_inizio = models.DateField(null=False,)
    data_fine = models.DateField(null=True, default=0)
    tipologia = models.CharField(max_length=1, choices=TIPOLOGIA, db_index=True)
    nome = models.CharField(max_length=50, blank=True, null=True)
    cognome = models.CharField(max_length=80, blank=True, null=True)
    motivo_commissariamento = models.CharField(max_length=500, blank=True, null=True)
    party_name = models.CharField(max_length=100, blank=True, null=True)
    party_acronym = models.CharField(max_length=50, blank=True, null=True)
    pic_url = models.URLField(blank=True, null=True, default = None)
    op_link = models.URLField(blank=True, null=True, default = None)

    @staticmethod
    def get_incarichi_attivi(territorio, anno):
        date_fmt = '%Y-%m-%d'
        jan_1_date = datetime.strptime(str(anno)+"-01-01", date_fmt).date()
        dec_31_date = datetime.strptime(str(anno)+"-12-31", date_fmt).date()

        return Incarico.objects.\
                filter(territorio=territorio,
                data_inizio__lte = dec_31_date,
                data_fine__gte = jan_1_date,
                )


    def __unicode__(self):
        return u"{0} - {1} - ({2}-{3})".format(self.territorio, self.cognome, self.data_inizio, self.data_fine,)