# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag("bilanci/confronti_parameter_list.html", takes_context=True)
def confronti_parameter_list(context, parameter_list_type, parameter_list, territorio_1_slug, territorio_2_slug):
    return {
        'parameter_list_type': parameter_list_type,
        'parameter_list': parameter_list,
        'territorio_1_slug':territorio_1_slug,
        'territorio_2_slug':territorio_2_slug,
    }