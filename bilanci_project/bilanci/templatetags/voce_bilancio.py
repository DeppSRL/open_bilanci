# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag("bilanci/bilanci_print.html", takes_context=True)
def bilanci_print(context, bilancio, voce, per_capita):

    if bilancio is None:
        return {
            'error': 'No data available!'
        }
    else:

        for bilancio_value in bilancio:
            if bilancio_value.voce == voce:
                if per_capita:
                    return_value = bilancio_value.valore_procapite
                else:
                    return_value = bilancio_value.valore

                return {
                    'value':return_value,
                }


