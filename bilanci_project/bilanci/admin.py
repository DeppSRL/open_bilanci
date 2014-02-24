from django.contrib import admin
from treeadmin.admin import TreeAdmin
from .models import Voce, ValoreBilancio

class VoceAdmin(TreeAdmin):
    model = Voce
    list_display = ['denominazione', 'slug']
    list_per_page = 400

admin.site.register(Voce, VoceAdmin)