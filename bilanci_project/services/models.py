from model_utils import Choices
from tinymce.models import HTMLField
from django.utils.translation import ugettext_lazy as _

__author__ = 'stefano'
# -*- coding: utf-8 -*-
from django.db import models
from territori.models import Territorio

class PaginaComune(models.Model):

    TIPOLOGIA = Choices(
        (u'0', u'LOGO', u'Logo senza nome Comune'),
        (u'1', u'TRADEMARK', u'Logo con nome Comune'),
    )

    host = models.TextField(blank=False, null=False, default='', help_text="IMPORTANT: use the format 'www.HOSTNAME.it' without http://")
    backlink = models.URLField(blank=False, null=False, default='')
    territorio = models.ForeignKey(Territorio, null=False, blank=False, db_index=True)
    header_text = HTMLField(_("Header text"), help_text=_("Testo che appare nella testata"), blank=True)
    footer_text = HTMLField(_("Footer text"), help_text=_("Testo che appare nel fondo pagina"), blank=True)
    logo = models.ImageField(null=True, blank=True, upload_to='comune_logo/')
    secondary_img = models.ImageField(null=True, blank=True, upload_to='secondary_img/')
    tipologia_logo = models.CharField(choices=TIPOLOGIA, max_length=2, null=False, blank=False, default=u'0')
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = u'Pagina Comune'

    def __unicode__(self):
        stato = 'Attivo'
        if not self.active:
            stato = 'Non attivo'
        return u"%s - %s" % (self.territorio.denominazione, stato)