# -*- coding: utf-8 -*-
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
import re
from bilanci.managers import ValoreBilancioManager, ValoreIndicatoreManager
from territori.models import Territorio


class VoceManager(models.Manager):
    def get_dict_by_slug(self):
        """
        Return a dict containing all the elements in the Voce model,
        having the slug as the key.

        :return: the dictionary
        """
        return dict([(v.slug, v) for v in self.all()])

class Voce(MPTTModel):
    objects = VoceManager()

    denominazione = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=256, blank=True, null=True, unique=True)

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')



    class MPTTMeta:
        order_insertion_by = ['denominazione']

    class Meta:
        verbose_name_plural = u'Voci'

    # model needed by TreeAdmin, to correctly show the denominazione
    # in the admin interface
    def short_title(self):
        return self.denominazione

    def indent_level(self):
        """
        Transform the node level into indentation level.
        Apply logic to handle various cases in different parts of the tree.
        """
        if re.match('preventivo-entrate', self.slug):
            return self.get_level() - 1

        if re.match('preventivo-spese', self.slug):
            if self.get_level() <= 2:
                return 0
            else:
                return self.get_level() - 3

        if re.match('consuntivo-entrate', self.slug):
            return self.get_level() - 1

        if re.match('consuntivo-spese', self.slug):
            if self.get_level() <= 4:
                return 0
            else:
                return self.get_level() - 4

        if re.match('consuntivo-spese', self.slug):
            if self.get_level() <= 3:
                return 0
            else:
                return self.get_level() - 3

        # default case
        return self.get_level() - 1



    def __unicode__(self):
        return u"%s" % (self.slug,)


class ValoreBilancio(models.Model):

    voce = models.ForeignKey(Voce, null=False, blank=False, db_index=True)
    territorio = models.ForeignKey(Territorio, null=False, blank=False, db_index=True)
    anno = models.PositiveSmallIntegerField(db_index=True)
    valore = models.BigIntegerField(default=0, null=True, blank=True)
    valore_procapite = models.FloatField(default=0., null=True, blank=True)

    objects = ValoreBilancioManager()

    def __unicode__(self):
        return u"%s %s %s" % (self.voce.denominazione, self.anno, self.valore)


class Indicatore(models.Model):
    denominazione = models.CharField(max_length=100)
    descrizione = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=256, blank=True, null=True, unique=True)
    published = models.BooleanField(default=True, blank=False, null=False)

    class Meta:
        verbose_name_plural = u'Indicatori'

    def __unicode__(self):
        return u"%s" % (self.denominazione,)



class ValoreIndicatore(models.Model):
    indicatore = models.ForeignKey(Indicatore)
    anno = models.PositiveIntegerField()
    territorio = models.ForeignKey(Territorio, null=False, blank=False)
    valore = models.FloatField(default=0.)

    objects = ValoreIndicatoreManager()

    class Meta:
        verbose_name_plural = u'Valori indicatori'
        unique_together = ('indicatore', 'anno', 'territorio', )

    def __unicode__(self):
        return u"%s: %s" % (self.indicatore, self.valore,)


class CodiceVoce(models.Model):
    voce = models.ForeignKey(Voce, null=False, blank=False, db_index=True)
    anno = models.PositiveSmallIntegerField(db_index=True)
    quadro = models.PositiveSmallIntegerField(db_index=True)
    colonna = models.PositiveSmallIntegerField(db_index=True)
    denominazione = models.TextField(max_length=1000)
