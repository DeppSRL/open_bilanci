from django.contrib import admin
from .models import PaginaComune

class PaginaComuneAdmin(admin.ModelAdmin):
    model = PaginaComune


admin.site.register(PaginaComune, PaginaComuneAdmin)