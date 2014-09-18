__author__ = 'stefano'
# -*- coding: utf-8 -*-
from django.db import models
from territori.models import Territorio

class PaginaComune(models.Model):

    host = models.TextField(blank=False, null=False, default=0)
    territorio = models.ForeignKey(Territorio, null=False, blank=False, db_index=True)
    header_text = models.TextField()
    footer_text = models.TextField()
    logo = models.FilePathField(null=True, blank=True)
    active = models.BooleanField(default=False)


    class Meta:
        verbose_name_plural = u'Pagina Comune'

    def __unicode__(self):
        return u"%s" % self.territorio.denominazione