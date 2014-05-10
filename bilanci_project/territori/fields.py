from django.conf import settings
from bilanci.models import ValoreBilancio
from territori.models import Territorio
from django_select2.fields import AutoModelSelect2Field


class TerritoriChoices(AutoModelSelect2Field):

    queryset =  Territorio.objects.filter(territorio = Territorio.TERRITORIO.C).\
                    order_by('-cluster', 'denominazione')


    search_fields = ['denominazione__icontains', ]

    def label_from_instance(self, obj):
        return obj.nome_con_provincia


class TerritoriClusterChoices(AutoModelSelect2Field):

    queryset =  Territorio.objects.filter(territorio = Territorio.TERRITORIO.C).\
                    order_by('-cluster', 'denominazione')

    search_fields = ['denominazione__icontains', ]


    def label_from_instance(self, obj):
        return u"{0} Cluster:{1}".format(obj.nome_con_provincia, obj.get_cluster_display())

