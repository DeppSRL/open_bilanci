# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.conf import settings
from model_utils import Choices
from django.contrib.gis.db import models
from datetime import datetime
import struct


class TerritoriManager(models.GeoManager):
    def nazione(self):
        return Territorio.objects.get(territorio=Territorio.TERRITORIO.N)

    @property
    def regioni(self, with_nation=False):
        codes = [Territorio.TERRITORIO.R]
        if with_nation:
            codes.append(Territorio.TERRITORIO.N)
            codes.append(Territorio.TERRITORIO.E)
        return self.get_query_set().filter(territorio__in=codes)

    @property
    def provincie(self):
        return self.get_query_set().filter(territorio=Territorio.TERRITORIO.P)

    @property
    def province(self):
        return self.provincie()

    @property
    def comuni(self):
        return self.get_query_set().filter(territorio=Territorio.TERRITORIO.C)

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
        return self.get_query_set().get(cod_reg=int(cod_reg), cod_prov=int(cod_prov),
                                        cod_com=str(int(cod_prov)) + cod_com)


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
        (u'1', u"0_500", u'Fino a 500 abitanti'),
        (u'2', u"501_1000", u'Da 501 a 1.000 abitanti'),
        (u'3', u"1001_3000", u'Da 1.001 a 3.000 abitanti'),
        (u'4', u"3001_5000", u'Da 3.001 a 5.000 abitanti'),
        (u'5', u"5001_10000", u'Da 5.001 a 10.000 abitanti'),
        (u'6', u"10001_50000", u'Da 10.001 a 50.000 abitanti'),
        (u'7', u"50001_200000", u'Da 50.001 a 200.000 abitanti'),
        (u'8', u"200001_500000", u'Da 200.001 a 500.000 abitanti'),
        (u'9', u"500001_", u'Oltre i 500.000 abitanti'),
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
            return u"{0} ({1})".format(self.nome, self.prov)


    def get_abitanti(self, anno=settings.TERRITORI_CONTEXT_REFERENCE_YEAR):
        try:
            contesto = self.contesto_set.get(anno=anno)

        except ObjectDoesNotExist:
            # if context isn't available for territori_context_reference_year ->
            # gets inhabitants n. from best year available
            latest_contesto = self.latest_contesto()
            if latest_contesto:
                return latest_contesto.bil_popolazione_residente
            else:
                return None

        else:
            return contesto.bil_popolazione_residente

    def best_year_voce(self, year, slug):

        # checks if the voice with the specified slug exists for a specific year,
        # if not return the closest previous year in which that voce was available
        available_years = self.valorebilancio_set.filter(voce__slug=slug).values_list('anno', flat=True).order_by(
            'anno')

        if not available_years:
            return None

        if year in available_years:
            return year
        else:

            best_year = available_years[0]
            year_differences = year - best_year

            # if supposed best yr is > year return none: this comparison is always backward
            if year_differences < 0:
                return None

            for considered_year in available_years:
                if year - considered_year < year_differences and year - considered_year > 0:
                    year_differences = year - considered_year
                    best_year = considered_year

            return best_year

    def best_year_indicatore(self, year, slug):

        # checks if the Indicatore with the specified slug exists for a specific year,
        # if not return the closest previous year in which that Indicatore was available
        available_years = self.valoreindicatore_set.filter(indicatore__slug=slug).values_list('anno',
                                                                                              flat=True).order_by(
            'anno')

        if not available_years:
            return None

        best_year = available_years[0]
        year_differences = year - best_year

        if year in available_years:
            return year
        else:

            for considered_year in available_years:
                if year - considered_year < year_differences and year - considered_year > 0:
                    year_differences = year - considered_year
                    best_year = considered_year

            return best_year


    def latest_year_indicatore(self, slug):
        available_years = list(
            self.valoreindicatore_set.filter(indicatore__slug=slug).values_list('anno', flat=True).order_by('anno'))

        if not available_years:
            return None

        return available_years[-1]

    def latest_contesto(self, anno=None):
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
                self.contesto_set.filter(bil_popolazione_residente__isnull=False). \
                    values_list('anno', 'bil_popolazione_residente')
            )
            if year in valid_pops:
                return (year, valid_pops[year])
            else:
                for i in range(1, 4):
                    if (year - i) in valid_pops:
                        return (year - 1, valid_pops[year - i])
                    elif (year + i) in valid_pops:
                        return (year + 1, valid_pops[year + i])

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
    def get_context(anno, territorio):
        """
        get territorio context record from Territorio, starting from year
        if a record for the chosen year is not found, the previous year is taken
        """
        comune_context = None

        while comune_context is None and anno >= settings.CLASSIFICHE_START_YEAR:
            try:
                comune_context = Contesto.objects.get(
                    anno=int(anno),
                    territorio=territorio,
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


class ParametriDeficitari(models.Model):
    # Deficitary values based on Quadro 50 - Consuntivo


    # 1) Valore negativo del risultato contabile di gestione superiore in termini di valore assoluto al 5% rispetto
    # alle entrate correnti (a tali fini al risultato contabile si aggiunge l'avanzo
    # di amministrazione utilizzato per le spese di investimento)
    valore_risultato_contabile = models.BooleanField(blank=False, null=False, default=False)

    # 2) Volume dei residui attivi di nuova formazione provenienti dalla gestione di competenza e relativi
    # ai titoli I e III, con esclusione dell'addizionale Irpef superiori al 42% dei valori di accertamento delle
    # entrate dei medesimi titoli I e III esclusi i valori dell'addizionale Irpef
    volume_residui_attivi = models.BooleanField(blank=False, null=False, default=False)

    # 3) Ammontare dei residui attivi di cui al titolo I e III superiori al 65% (provenienti dalla gestione dei
    # residui attivi) rapportati agli accertamenti della gestione di competenza delle entrate dei medesimi titolo I e III
    ammontare_residui_attivi = models.BooleanField(blank=False, null=False, default=False)

    # 4) Volume dei residui passivi complessivi provenienti dal titolo I superiori al 40% degli impegni della medesima spesa corrente
    volume_residui_passivi = models.BooleanField(blank=False, null=False, default=False)

    # 5) Esistenza di procedimenti di esecuzione forzata superiori allo 0,5% delle spese correnti
    esistenza_di_procedimenti = models.BooleanField(blank=False, null=False, default=False)

    # 6) Volume complessivo delle spese di personale a vario titolo rapportato al volume complessivo delle entrate
    # correnti desumibili dai titoli I, II e III superiore al 40% per i comuni inferiori a 5.000 abitanti,
    # superiore al 39% per i comuni da 5.000 a 29.999 abitanti e superiore al 38% per i comuni oltre i 29.999 abitanti
    # (al netto dei contributi regionali nonchè di altri enti pubblici finalizzati a finanziare spese di personale)
    volume_spese_personale = models.BooleanField(blank=False, null=False, default=False)

    # 7) Consistenza dei debiti di finanziamento non assistiti da contribuzioni superiore al 150% rispetto
    # alle entrate correnti per gli enti che presentano un risultato contabile di gestione positivo superiore al 120%
    # per gli enti che presentano un risultato contabile di gestione negativo (fermo restando il rispetto del
    # limite di indebitamento di cui all'art. 204 del touel)
    consistenza_debiti_finanziamento = models.BooleanField(blank=False, null=False, default=False)

    # 8) Consistenza dei debiti fuori bilancio formatisi nel corso dell'esercizio superiore all'1% rispetto ai valori
    # di accertamento delle entrate correnti (l'indice si considera negativo ove tale
    # soglia venga superata in tutti gli ultimi tre anni)
    consistenza_debiti_fuori_bilancio = models.BooleanField(blank=False, null=False, default=False)

    # 9) Eventuale esistenza al 31 dicembre di anticipazioni di tesoreria non rimborsate superiori al 5%
    # rispetto alle entrate correnti
    anticipazioni_tesoreria = models.BooleanField(blank=False, null=False, default=False)

    # 10) Ripiano squilibri in sede di provvedimento di salvaguardia di cui all'art. 193 del touel riferito allo stesso
    # esercizio con misure di alienazione di beni patrimoniali e/o avanzo di amministrazione superiore
    # al 5% dei valori della spesa corrente
    ripiano_squilibri = models.BooleanField(blank=False, null=False, default=False)

    territorio = models.ForeignKey(Territorio, blank=False, null=False)
    anno = models.PositiveSmallIntegerField(null=False, default=0)


class Incarico(models.Model):
    ##
    # Caches the Incarico data from Open Politici API for each Territorio
    ##

    TIPOLOGIA = Choices(
        (u'1', u"sindaco", u'Sindaco'),
        (u'2', u"commissario", u'Commissario'),
        (u'3', u"vicesindaco_ff", u'Vicesindaco f.f.'),
    )

    territorio = models.ForeignKey(Territorio, null=False, default=0)

    data_inizio = models.DateField(null=False, db_index=True)
    data_fine = models.DateField(null=True, default=0, db_index=True)
    tipologia = models.CharField(max_length=1, choices=TIPOLOGIA, db_index=True)
    nome = models.CharField(max_length=50, blank=True, null=True)
    cognome = models.CharField(max_length=80, blank=True, null=True)
    motivo_commissariamento = models.CharField(max_length=500, blank=True, null=True)
    party_name = models.CharField(max_length=100, blank=True, null=True)
    party_acronym = models.CharField(max_length=50, blank=True, null=True)
    pic_url = models.URLField(blank=True, null=True, default=None)
    op_link = models.URLField(blank=True, null=True, default=None)

    @staticmethod
    def get_incarichi_attivi(territorio, anno):
        date_fmt = '%Y-%m-%d'
        jan_1_date = datetime.strptime(str(anno) + "-01-01", date_fmt).date()
        dec_31_date = datetime.strptime(str(anno) + "-12-31", date_fmt).date()

        return Incarico.objects. \
            filter(
            Q(territorio=territorio),
            Q(data_inizio__lte=dec_31_date),
            Q(data_fine__gte=jan_1_date) | Q(data_fine__isnull=True),
        )


    @staticmethod
    def get_incarichi_attivi_set(territorio_set, anno):
        date_fmt = '%Y-%m-%d'
        jan_1_date = datetime.strptime(str(anno) + "-01-01", date_fmt).date()
        dec_31_date = datetime.strptime(str(anno) + "-12-31", date_fmt).date()

        return Incarico.objects. \
            filter(Q(territorio__in=territorio_set),
                   Q(data_inizio__lte=dec_31_date),
                   Q(data_fine__gte=jan_1_date) | Q(data_fine__isnull=True),
        )


    def __unicode__(self):
        return u"{0} - {1} - ({2}-{3})".format(self.territorio, self.cognome, self.data_inizio, self.data_fine, )