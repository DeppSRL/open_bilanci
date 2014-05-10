from django.conf import settings
from bilanci.models import ValoreBilancio
from territori.models import Territorio, Contesto
from django_select2.fields import AutoModelSelect2Field

class TerritoriChoices(AutoModelSelect2Field):
    #
    # queryset = Territorio.objects.\
    #             filter(territorio=Territorio.TERRITORIO.C).\
    #             exclude( valorebilancio__isnull=True).\
    #             order_by('-cluster', 'denominazione')

    vb = ValoreBilancio.objects.filter(territorio__territorio=Territorio.TERRITORIO.C).\
        filter(anno=2013,voce__slug='preventivo').values_list('territorio__pk',flat=True)

    queryset =  Territorio.objects.filter(pk__in=vb).\
        order_by('-cluster','denominazione')


    search_fields = ['denominazione__icontains', ]

    def label_from_instance(self, obj):
        return obj.nome_con_provincia


class TerritoriClusterChoices(AutoModelSelect2Field):

    queryset =  Territorio.objects.filter(territorio = Territorio.TERRITORIO.C).\
                    exclude( valorebilancio__isnull=True).\
                    order_by('-cluster', 'denominazione')

    search_fields = ['denominazione__icontains', ]


    def label_from_instance(self, obj):
        return u"{0} Cluster:{1}".format(obj.nome_con_provincia, obj.get_cluster_display())

