from django.contrib import admin
from treeadmin.admin import TreeAdmin
from .models import Voce, CodiceVoce, Indicatore, ImportXmlBilancio


class VoceAdmin(TreeAdmin):
    model = Voce
    search_fields = ['slug', ]
    list_display = ['denominazione', 'slug']
    list_per_page = 1000


class ImportXmlBilancioAdmin(admin.ModelAdmin):
    ordering = ('-created_at', 'territorio__denominazione')


class IndicatoreAdmin(admin.ModelAdmin):
    ordering = ('-published', 'denominazione')
    list_filter = ('published',)


class CodiceVoceAdmin(admin.ModelAdmin):
    ordering = ('anno', 'voce__slug')
    search_fields = ('voce__slug', 'voce__denominazione')
    list_filter = ('anno',)


admin.site.register(Voce, VoceAdmin)
admin.site.register(CodiceVoce, CodiceVoceAdmin)
admin.site.register(Indicatore, IndicatoreAdmin)
admin.site.register(ImportXmlBilancio, ImportXmlBilancioAdmin)