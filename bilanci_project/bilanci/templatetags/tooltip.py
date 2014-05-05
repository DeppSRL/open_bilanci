# -*- coding: utf-8 -*-
__author__ = 'stefano'
from django import template

register = template.Library()

##
# shows a clickable tooltip icon
##

@register.inclusion_tag("bilanci/tooltip.html", takes_context=True)
def tooltip(context,**kwargs):
    return kwargs
