from django.contrib.gis import admin
from .models import Territorio, Contesto

class TerritorioAdmin(admin.OSMGeoAdmin):
    list_filter = ('territorio',)
    search_fields = ('denominazione',)
    prepopulated_fields = {"slug": ("denominazione",)}

class ContestoAdmin(admin.ModelAdmin):
    list_filter = ('anno',)
    ordering = ('territorio__denominazione',)

admin.site.register(Territorio, TerritorioAdmin)
admin.site.register(Contesto, ContestoAdmin)