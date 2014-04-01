# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag("bilanci/classifiche_incarichi_politici.html", takes_context=True)

def classifiche_incarichi_politici(context, valore_obj):

    return {
        'valore_obj': valore_obj,
    }
