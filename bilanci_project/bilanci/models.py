# -*- coding: utf-8 -*-
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from territori.models import Territorio


class Voce(MPTTModel):
    denominazione = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=128, blank=True, null=True, unique=True)

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['denominazione']

    class Meta:
        verbose_name_plural = u'Voci'

    def __unicode__(self):
        return u"%s" % (self.denominazione,)


class ValoreBilancio(models.Model):

    voce = models.ForeignKey(Voce, null=False, blank=False)
    territorio = models.ForeignKey(Territorio, null=False, blank=False)

    anno = models.PositiveSmallIntegerField()

    valore = models.BigIntegerField(default=0, null=True, blank=True)









