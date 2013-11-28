from django.db import models
from model_utils import Choices
from mptt.models import MPTTModel, TreeForeignKey


class Ente(models.Model):

    name = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=45, blank=True)

class Voce(MPTTModel):
    denominazione = models.CharField(max_length=100)
    descrizione = models.TextField(max_length=500)

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['denominazione']

    class Meta:
        verbose_name_plural = u'Voci'

    def __unicode__(self):
        return u"%s" % (self.denominazione,)


class Valore(models.Model):

    anno = models.IntegerField()
    voce = models.ForeignKey(Voce, null=False, blank=False)
    valore = models.DecimalField(decimal_places=2, max_digits=15, default=0.00, null=True, blank=True)

    class Meta:
        abstract = True


class ValoreBilanciComunali(Valore):

    TIPO_CERTIFICATO = Choices(
        ('0', 'Preventivo'),
        ('1', 'Consuntivo'),
        )

    tipo_certificato = models.CharField(max_length=2, choices=TIPO_CERTIFICATO, default='0')
    ente = models.ForeignKey(Ente)

    class Meta:
        abstract = True



class Spesa(ValoreBilanciComunali):

    TIPO_SPESA = Choices(
        ('0', 'Corrente'),
        ('1', 'Conto capitale'),
    )

    TIPO_ESBORSO = Choices(
        ('0', 'Impegni'),
        ('1', 'Conto competenza'),
        ('2', 'Conto residui'),
        ('3', 'Preventivato'),
        )

    tipo_spesa = models.CharField(max_length=2, choices=TIPO_SPESA)
    tipo_esborso = models.CharField(max_length=2, choices=TIPO_ESBORSO, default='0')


    class Meta:
        verbose_name_plural = u'Spese'

    def __unicode__(self):
        return u"%s" % (self.voce.denominazione,)


class Entrata(ValoreBilanciComunali):

    class Meta:
        verbose_name_plural = u'Entrate'

    def __unicode__(self):
        return u"%s" % (self.voce.denominazione,)


