from territori.models import Territorio
from django_select2.fields import AutoModelSelect2Field

class TerritoriChoices(AutoModelSelect2Field):
    queryset = Territorio.objects.filter(territorio='C').order_by('-abitanti')
    search_fields = ['denominazione__icontains', ]

    def label_from_instance(self, obj):
        return obj.nome_con_provincia


class TerritoriClusterChoices(AutoModelSelect2Field):
    queryset = Territorio.objects.filter(territorio='C').order_by('-abitanti')
    search_fields = ['denominazione__icontains', ]

    def label_from_instance(self, obj):
        return obj.nome_con_provincia +" ("+ obj.get_cluster_display()+")"
