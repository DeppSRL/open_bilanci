from django.contrib import admin
from .models import PaginaComune
from services.forms import PaginaComuneAdminForm


class PaginaComuneAdmin(admin.ModelAdmin):
    model = PaginaComune
    form = PaginaComuneAdminForm


admin.site.register(PaginaComune, PaginaComuneAdmin)