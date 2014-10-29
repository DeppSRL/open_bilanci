# -*- coding: utf-8 -*-
__author__ = 'stefano'
from django import template

register = template.Library()

##
# section values type display a the type of values shown
##

@register.inclusion_tag("bilanci/_section_values_type.html", takes_context=True)
def section_values_type(context,**kwargs):
    return kwargs
