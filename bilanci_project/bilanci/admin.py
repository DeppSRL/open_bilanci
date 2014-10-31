from django.contrib import admin
from treeadmin.admin import TreeAdmin
from .models import Voce, CodiceVoce, Indicatore

class VoceAdmin(TreeAdmin):
    model = Voce
    search_fields = ['slug',]
    list_display = ['denominazione', 'slug']
    list_per_page = 1000

class IndicatoreAdmin(admin.ModelAdmin):
    ordering = ('-published', 'denominazione')
    list_filter = ('published',)
    pass

class CodiceVoceAdmin(admin.ModelAdmin):
    pass

admin.site.register(Voce, VoceAdmin)
admin.site.register(CodiceVoce, CodiceVoceAdmin)
admin.site.register(Indicatore, IndicatoreAdmin)