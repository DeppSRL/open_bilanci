# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag("bilanci/voce_valore.html", takes_context=True)
def voce_valore(context, bilancio_valori, considered_voce):

    if bilancio_valori is None:
        return {
            'value': None
        }

    if "totale" not in considered_voce.denominazione.lower():
        for bilancio_value in bilancio_valori:
            # cerca nel bilancio il valore corrispondente alla voce che ci interessa
            if bilancio_value.voce == considered_voce:
                return {
                    'valore': bilancio_value.valore,
                    'valore_procapite': bilancio_value.valore_procapite
                }



