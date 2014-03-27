# -*- coding: utf-8 -*-

from django import template

register = template.Library()

def comma2dot(value):
    return value.replace(",", ".")
register.filter('comma2dot', comma2dot)

@register.inclusion_tag("bilanci/_voice_values.html", takes_context=True)
def voice_values(context, voice_slug, values):

    if "spese-correnti" in voice_slug:
        inv_voice_slug = voice_slug.replace("spese-correnti", "spese-per-investimenti")
        absolute_value = values['absolute'][voice_slug] + values['absolute'][inv_voice_slug]
        percapita_value = values['percapita'][voice_slug] + values['percapita'][inv_voice_slug]
    else:
        absolute_value = values['absolute'][voice_slug]
        percapita_value = values['percapita'][voice_slug]

    return {
        'absolute_value': absolute_value,
        'percapita_value': percapita_value,
    }


@register.inclusion_tag("bilanci/_voice_composition.html", takes_context=True)
def voice_composition(context, voice_slug, values):

    if "interventi" in voice_slug.lower():
        return {}

    inv_voice_slug = voice_slug.replace("spese-correnti", "spese-per-investimenti")

    correnti = float(values['absolute'][voice_slug])
    investimenti = float(values['absolute'][inv_voice_slug])
    total = correnti + investimenti

    if total:
        correnti_perc = correnti / total * 100.0
        investimenti_perc = investimenti / total * 100.0
    else:
        correnti_perc = 0.0
        investimenti_perc = 0.0

    return {
        'correnti_value': correnti,
        'correnti_perc': correnti_perc,
        'investimenti_value': investimenti,
        'investimenti_perc': investimenti_perc,
    }


