from django.conf import settings
from territori.models import Territorio, Contesto
from django_select2.fields import AutoModelSelect2Field

class TerritoriChoices(AutoModelSelect2Field):


    queryset = Territorio.objects.\
                filter(contesto__anno = settings.REFERENCE_YEAR).\
                filter(territorio=Territorio.TERRITORIO.C).\
                order_by('-contesto__bil_popolazione_residente', 'denominazione')

    search_fields = ['denominazione__icontains', ]

    def label_from_instance(self, obj):
        return obj.nome_con_provincia


class TerritoriClusterChoices(AutoModelSelect2Field):

    queryset = Territorio.objects.\
                filter(contesto__anno = settings.REFERENCE_YEAR).\
                filter(territorio=Territorio.TERRITORIO.C).\
                order_by('-contesto__bil_popolazione_residente', 'denominazione')

    search_fields = ['denominazione__icontains', ]


    def label_from_instance(self, obj):
        return u"{0} Cluster:{1}".format(obj.nome_con_provincia, obj.get_cluster_display())

