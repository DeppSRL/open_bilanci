# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag("bilanci/classifiche_parameter_list.html", takes_context=True)

def classifiche_parameter_list(context, parameter_list_type, parameter_list, selected_par_type, selected_par_slug, selected_year):

    return {
        'parameter_list_type': parameter_list_type,
        'parameter_list': parameter_list,
        # selected parameter type / selected parameter slug
        'selected_par_type': selected_par_type,
        'selected_par_slug': selected_par_slug,
        'selected_year': selected_year,

    }
