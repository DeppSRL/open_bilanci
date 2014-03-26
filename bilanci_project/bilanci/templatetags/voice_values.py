# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag("bilanci/_voice_values.html", takes_context=True)
def voce_valore(context, voice_slug, values):
    absolute_value = values['absolute'][voice_slug]
    percapita_value = values['percapita'][voice_slug],
    total_value = absolute_value + percapita_value
    return {
        'absolute_value': absolute_value,
        'percapita_value': percapita_value,
    }



