# -*- coding: utf-8 -*-

from django import template
import hashlib

register = template.Library()

def comma2dot(value):
    return value.replace(",", ".")
register.filter('comma2dot', comma2dot)

@register.inclusion_tag("bilanci/_voice_values.html", takes_context=True)
def voice_values(context, voice_slug, values, is_interventi=False):
    """
    Compute the values for the given voice_slug.
    is_interventi is a flag, set to True when the tag is called
                  within an interventi view
    """
    absolute_value = ''
    percapita_value = ''

    if voice_slug in values['absolute'].keys():
            absolute_value = values['absolute'][voice_slug]

    if voice_slug in values['percapita'].keys():
        percapita_value = values['percapita'][voice_slug]

    return {
        'absolute_value': absolute_value,
        'percapita_value': percapita_value,
    }


@register.inclusion_tag("bilanci/_voice_composition.html", takes_context=True)
def voice_composition(context, voice_slug, values):

    # from the voce slug (in the somma funzioni branch) gets the investimenti and spese correnti values
    # and computes the % of investment of the voice

    if "interventi" in voice_slug.lower():
        return {}
    subslug_somma_funzioni = 'spese-somma-funzioni'

    investimenti_voice_slug = voice_slug.replace(subslug_somma_funzioni, "spese-per-investimenti-funzioni")
    correnti_voice_slug = voice_slug.replace(subslug_somma_funzioni, "spese-correnti-funzioni")

    if voice_slug in values['absolute'].keys():
        correnti = float(values['absolute'][correnti_voice_slug])

        if investimenti_voice_slug in values['absolute'].keys():
            investimenti = float(values['absolute'][investimenti_voice_slug])
            total = values['absolute'][voice_slug]

            if total:
                correnti_perc = correnti / total * 100.0
                investimenti_perc = investimenti / total * 100.0
            else:
                correnti_perc = 0.0
                investimenti_perc = 0.0

            return {
                'hash': hashlib.sha512(voice_slug).hexdigest()[:8],
                'correnti_value': correnti,
                'correnti_perc': correnti_perc,
                'investimenti_value': investimenti,
                'investimenti_perc': investimenti_perc,
            }
