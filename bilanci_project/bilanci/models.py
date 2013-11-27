from django.db import models
from model_utils import Choices
from mptt.models import MPTTModel, TreeForeignKey

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


class Spesa(Valore):

    TIPO_SPESA = Choices(
        ('0', 'Corr'),
        ('1', 'Conto capitale'),
    )

    tipo_spesa = models.CharField(max_length=2, choices=TIPO_SPESA)

    class Meta:
        verbose_name_plural = u'Spese'

    def __unicode__(self):
        return u"%s" % (self.voce.denominazione,)

