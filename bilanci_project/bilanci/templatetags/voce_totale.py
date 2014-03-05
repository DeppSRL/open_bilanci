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
    voce_children = []
    for voce_son in considered_voce.get_children():
        voce_children.append(voce_son)
        if "totale" in voce_son.denominazione.lower():

            # se ha trovato un nodo figlio il cui nome contiene "totale"
            # cerca il valore corrispondente e lo ritorna
            for value in bilancio_valori:

                if value.voce == voce_son:

                    return {
                        'valore': value.valore,
                        'valore_procapite': value.valore_procapite,
                    }


    # se non ha trovato una voce "totale" allora calcola la somma di tutti i figli
    # e ritorna quel valore
    valore = 0
    valore_procapite = 0

    for voce_child in voce_children:
        for value in bilancio_valori:
            if value.voce == voce_child:
                valore += value.valore
                valore_procapite += value.valore_procapite


    return {
        'valore': valore,
        'valore_procapite': valore_procapite,
    }


