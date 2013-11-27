from django.contrib import admin
from .models import Voce, Spesa

class VoceAdmin(admin.ModelAdmin):
    model = Voce

class SpesaAdmin(admin.ModelAdmin):
    model = Spesa


admin.site.register(Voce, VoceAdmin)
admin.site.register(Spesa, SpesaAdmin)
