from territori.models import Territorio, Contesto
from django_select2.fields import AutoModelSelect2Field

class TerritoriChoices(AutoModelSelect2Field):


    queryset = Territorio.objects.\
                filter(contesto__anno = 2012).\
                filter(territorio=Territorio.TERRITORIO.C).\
                order_by('-contesto__istat_abitanti', 'denominazione')

    search_fields = ['denominazione__icontains', ]

    def label_from_instance(self, obj):
        return obj.nome_con_provincia


class TerritoriClusterChoices(AutoModelSelect2Field):
    search_fields = ['denominazione__icontains', ]


    def label_from_instance(self, obj):
        return obj.nome_con_provincia +" ("+ obj.get_cluster_display()+")"
