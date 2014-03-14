# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from model_utils import Choices
from django.contrib.gis.db import models
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
        ('C', 'Comune'),
        ('P', 'Provincia'),
        ('R', 'Regione'),
        ('N', 'Nazionale'),
        ('E', 'Estero'),
        ('L', 'Cluster'),
        )

    CLUSTER = Choices(
        ('1',"i_piu_piccoli", 'I più piccoli'),
        ('2', "molto_piccoli", 'Molto piccoli'),
        ('3', "piccoli_1", 'Piccoli 1'),
        ('4', "piccoli_2", 'Piccoli 2'),
        ('5', "medio_piccoli", 'Medio piccoli'),
        ('6', "medi", 'Medi'),
        ('7', "grandi", 'Grandi'),
        ('8', "molto_grandi", 'Molto grandi'),
        ('9', "i_piu_grandi", 'I più grandi'),
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
        if self.territorio == 'C':
            return self.cod_com
        elif self.territorio == 'P':
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
            return self.nome

    def __unicode__(self):
        return self.denominazione

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

    ##
    # NOTE: bil_popolazione_residente is deprecated, actual field is istat_abitanti
    ##

    bil_popolazione_residente = models.IntegerField(null=True, default=None, blank=True)
    bil_strade_esterne = models.IntegerField(null=True, default=None, blank=True)
    bil_strade_interne = models.IntegerField(null=True, default=None, blank=True)
    bil_strade_montane = models.IntegerField(null=True, default=None, blank=True)

    istat_abitanti = models.IntegerField(null=True, default=None, blank=True)

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
        return "{0} ({1})".format(self.territorio, self.anno)

    class Meta:
        verbose_name = u'Contesto'
        verbose_name_plural = u'Contesti'
        ordering = ['territorio']
