# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q
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

    # get_natural_descendants:
    # given a Voce returns the descendants of such node
    # filtering out the nodes in branches which are computed:
    # the CASSA branch and the SOMMA-FUNZIONI branch

    def get_natural_descendants(self):
        return self.get_descendants(include_self=False).\
            exclude(
                Q(slug__startswith="consuntivo-spese-cassa") |
                Q(slug__startswith="consuntivo-entrate-cassa")).\
            exclude(
                Q(slug__startswith="preventivo-spese-spese-somma-funzioni") |
                Q(slug__startswith="consuntivo-spese-impegni-spese-somma-funzioni") |
                Q(slug__startswith="consuntivo-spese-cassa-spese-somma-funzioni")
            )

    # get_natural_children:
    # given a Voce returns the children of such node
    # filtering out the nodes in branches which are computed:
    # the CASSA branch and the SOMMA-FUNZIONI branch

    def get_natural_children(self):
        return self.get_children().\
            exclude(
                Q(slug__startswith="consuntivo-spese-cassa") |
                Q(slug__startswith="consuntivo-entrate-cassa")).\
            exclude(
                Q(slug__startswith="preventivo-spese-spese-somma-funzioni") |
                Q(slug__startswith="consuntivo-spese-impegni-spese-somma-funzioni") |
                Q(slug__startswith="consuntivo-spese-cassa-spese-somma-funzioni")
            )


    # get_components_cassa:
    # for the Voce in the spese-cassa branch
    # returns the Voce that are components of that Voce.
    # For CASSA elements: return Conto-residui and Conto-competenza Voce

    def get_components_cassa(self):
        cassa_branches = ["consuntivo-spese-cassa", "consuntivo-entrate-cassa"]
        c_residui_prefixes = ["consuntivo-spese-pagamenti-in-conto-residui","consuntivo-entrate-riscossioni-in-conto-residui"]
        c_competenza_prefixes = ["consuntivo-spese-pagamenti-in-conto-competenza","consuntivo-entrate-riscossioni-in-conto-competenza"]

        cassa_branch_set = filter((lambda x: x in self.slug), cassa_branches)
        if cassa_branch_set > 0:
            cassa_branch = cassa_branch_set[0]
            i = 1

            if cassa_branch == cassa_branches[0]:
                i = 0
            elif cassa_branch != cassa_branches[1]:
                # this should NOT HAPPEN, ERROR
                raise BaseException

            c_residui = c_residui_prefixes[i]
            c_competenza = c_competenza_prefixes[i]

            slug_residui = self.slug.replace(cassa_branch, c_residui )
            slug_competenza = self.slug.replace(cassa_branch, c_competenza)

            return Voce.objects.filter(slug__in = [slug_residui, slug_competenza])

        return None


    # get_components_somma_funzioni
    # for the Voce in the somma-funzioni branch
    # returns the Voce that are components of that Voce.
    # For SPESE-SOMMA-FUNZIONI elements: return Spese-correnti and Spese-per-investimenti Voce

    def get_components_somma_funzioni(self):
        somma_funzioni_prefix = "spese-somma-funzioni"
        somma_funzioni_branches = [
            "preventivo-spese-spese-somma-funzioni",
            "consuntivo-spese-cassa-spese-somma-funzioni",
            "consuntivo-spese-impegni-spese-somma-funzioni"
        ]

        spese_correnti_prefix = "spese-correnti-funzioni"
        spese_investimenti_prefix = "spese-per-investimenti-funzioni"
        if filter((lambda x: x in self.slug), somma_funzioni_branches) > 0:
            slug_correnti = self.slug.replace(somma_funzioni_prefix, spese_correnti_prefix)
            slug_investimenti= self.slug.replace(somma_funzioni_prefix, spese_investimenti_prefix)
            return Voce.objects.filter(slug__in = [slug_correnti, slug_investimenti])

        return None



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


##
# CodiceVoce: maps Xml bilancio codes to simplified bilancio Voce
##
class CodiceVoce(models.Model):
    voce = models.ForeignKey(Voce, null=False, blank=False, db_index=True)
    anno = models.PositiveSmallIntegerField(db_index=True)
    quadro_cod = models.CharField(max_length=5, null=False, blank=False, default='')
    voce_cod = models.CharField(max_length=5, null=False, blank=False, default='')
    colonna_cod = models.CharField(max_length=5, null=False, blank=False, default='')
    denominazione_voce = models.TextField(max_length=1000)
    denominazione_colonna = models.TextField(max_length=100)

    class Meta:
        verbose_name_plural = u'Codici voce'

    def __unicode__(self):
        if self.colonna_cod:
            return u"%s - %s (%s-%s-%s)" % (self.anno, self.voce.slug, self.quadro_cod, self.voce_cod, self.colonna_cod)
        else:
            return u"%s - %s (%s-%s)" % (self.anno, self.voce.slug, self.quadro_cod, self.voce_cod,)

    @staticmethod
    def get_bilancio_codes(anno, tipo_certificato):

        return CodiceVoce.objects.filter(anno=anno,voce__slug__startswith=tipo_certificato).order_by('voce__slug')