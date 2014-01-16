from territori.models import Territorio
from django_select2.fields import AutoModelSelect2Field

class TerritoriChoices(AutoModelSelect2Field):
    queryset = Territorio.objects.order_by('denominazione')
    search_fields = ['denominazione__icontains', ]

    def label_from_instance(self, obj):
        return obj.slug