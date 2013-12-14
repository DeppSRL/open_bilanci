from django.contrib import admin
from treeadmin.admin import TreeAdmin
from .models import Voce, Spesa, Entrata, Ente

class VoceAdmin(TreeAdmin):
    model = Voce

admin.site.register(Voce, VoceAdmin)
