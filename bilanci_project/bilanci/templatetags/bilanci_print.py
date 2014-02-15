# -*- coding: utf-8 -*-

from django import template

register = template.Library()

def bilanci_print(context, bilancio, anno, tipo):

    if bilancio is None:
        return {
            'error': 'No data available!'
        }
    else:
        return {
            'bilancio': bilancio[str(anno)][str(tipo)],
        }

register.inclusion_tag("bilanci/bilanci_print.html", takes_context=True)(bilanci_print)

