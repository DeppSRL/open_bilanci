from django.contrib import admin
from treeadmin.admin import TreeAdmin
from .models import Voce, ValoreBilancio, Indicatore

class VoceAdmin(TreeAdmin):
    model = Voce
    list_display = ['denominazione', 'slug']
    list_per_page = 1000

class IndicatoreAdmin(admin.ModelAdmin):
    pass


admin.site.register(Voce, VoceAdmin)
admin.site.register(Indicatore, IndicatoreAdmin)