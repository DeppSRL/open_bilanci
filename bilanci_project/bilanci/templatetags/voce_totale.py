# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag("bilanci/voce_totale.html", takes_context=True)
def voce_totale(context, bilancio_valori, considered_voce, inhabitants):

    if bilancio_valori is None:
        return {
            'value': 'No data available!'
        }


    # una volta trovata la voce che ci interessa:
    # se fra i figli una voce che contiene la stringa "totale" quello sara' il valore ritornato
    # se non c'e' il totale sara' la somma degli importi dei figli

    for voce_son in considered_voce.get_children():
        if "totale" in voce_son.denominazione.lower():

            for value in bilancio_valori:

                if value.voce == voce_son:


                    return {
                        'valore': value.valore,
                        'valore_procapite': value.valore_procapite
                    }


    return {
        'valore':'somma'
    }