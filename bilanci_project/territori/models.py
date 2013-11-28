# -*- coding: utf-8 -*-

from model_utils import Choices
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
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
        )
    cod_reg = models.IntegerField(default=0, blank=True, null=True, db_index=True)
    cod_prov = models.IntegerField(default=0, blank=True, null=True, db_index=True)
    cod_com = models.IntegerField(default=0, blank=True, null=True, db_index=True)
    denominazione = models.CharField(max_length=128, db_index=True)
    denominazione_ted = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    slug = models.SlugField(max_length=256, null=True, blank=True)
    territorio = models.CharField(max_length=1, choices=TERRITORIO, db_index=True)
    geom = models.MultiPolygonField(srid=4326, null=True, blank=True)
    popolazione_totale = models.IntegerField(null=True, blank=True)
    popolazione_maschile = models.IntegerField(null=True, blank=True)
    popolazione_femminile = models.IntegerField(null=True, blank=True)

    objects = TerritoriManager()


    @property
    def codice(self):
        if self.territorio == 'C':
            return self.cod_com
        elif self.territorio == 'P':
            return self.cod_prov
        else:
            return self.cod_reg

    @property
    def code(self):
        return self.get_cod_dict().values()[0]

    def get_cod_dict(self, prefix=''):
        """
        return a dict with {prefix}cod_{type} key initialized with correct value
        """
        if self.territorio == self.TERRITORIO.R:
            return { '{0}cod_reg'.format(prefix): self.cod_reg }
        elif self.territorio == self.TERRITORIO.P:
            return { '{0}cod_prov'.format(prefix): self.cod_prov }
        elif self.territorio == self.TERRITORIO.C:
            return { '{0}cod_com'.format(prefix) : self.cod_com }
        elif self.territorio == self.TERRITORIO.N:
            return { '{0}cod_reg'.format(prefix): 0 }
        elif self.territorio == self.TERRITORIO.E:
            return { '{0}pk'.format(prefix): self.pk }

        raise Exception('Territorio non interrogabile %s' % self)

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
        if self.denominazione_ted:
            return u"%s - %s" % (self.denominazione, self.denominazione_ted)
        else:
            return u"%s" % self.denominazione


    @property
    def nome_con_provincia(self):
        if self.territorio == self.TERRITORIO.P:
            return u"{0} (Provincia)".format(self.nome)
        else:
            return self.nome

    @property
    def ambito_territoriale(self):
        """
        returns: a Region (for C,P or R), Nazionale, or Estero
        """
        if self.territorio == self.TERRITORIO.R:
            return self.nome
        elif self.territorio == self.TERRITORIO.P or self.territorio == self.TERRITORIO.C:
            regione = Territorio.objects.regioni().get(cod_reg=self.cod_reg)
            return regione.nome
        elif self.territorio == self.TERRITORIO.N:
            return 'Nazionale'
        else:
            return 'Estero'

    def __unicode__(self):
        return self.nome


    @models.permalink
    def get_absolute_url(self):
        url_name = 'territori_{0}'.format({
            self.TERRITORIO.R: 'regione',
            self.TERRITORIO.P: 'provincia',
            self.TERRITORIO.C: 'comune',
            self.TERRITORIO.N: 'nazionale',
            self.TERRITORIO.E: 'estero',
            }[self.territorio])
        if self.territorio in (Territorio.TERRITORIO.N, Territorio.TERRITORIO.E):
            return url_name
        return (url_name, (), {
            'slug': self.slug
        })

    class Meta:
        verbose_name = u'Località'
        verbose_name_plural = u'Località'
        ordering = ['denominazione']

