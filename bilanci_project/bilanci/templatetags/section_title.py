# -*- coding: utf-8 -*-
__author__ = 'stefano'
from django import template

register = template.Library()

##
# section title display a content title for different pages
##

@register.inclusion_tag("bilanci/section_title.html", takes_context=True)
def section_title(context,**kwargs):
    return kwargs
