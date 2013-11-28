from django.contrib import admin
from .models import Voce, Spesa, Entrata, Ente

class VoceAdmin(admin.ModelAdmin):
    model = Voce

class SpesaAdmin(admin.ModelAdmin):
    model = Spesa


class EntrataAdmin(admin.ModelAdmin):
    model = Entrata



admin.site.register(Voce, VoceAdmin)
admin.site.register(Spesa, SpesaAdmin)
admin.site.register(Entrata, EntrataAdmin)
