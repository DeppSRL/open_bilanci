from territori.models import Territorio, Contesto
from django_select2.fields import AutoModelSelect2Field

class TerritoriChoices(AutoModelSelect2Field):
    # queryset = Territorio.objects.filter(territorio='C').order_by('-abitanti')
    queryset = Contesto.objects.filter(anno=2012).filter(territorio__territorio='C').\
                order_by('-istat_abitanti')
    search_fields = ['territorio__denominazione__icontains', ]

    def label_from_instance(self, obj):
        return obj.territorio.nome_con_provincia


class TerritoriClusterChoices(AutoModelSelect2Field):
    search_fields = ['territorio__denominazione__icontains', ]


    def label_from_instance(self, obj):
        return obj.territorio.nome_con_provincia +" ("+ obj.territorio.get_cluster_display()+")"
