# -*- coding: utf-8 -*-
__author__ = 'stefano'
from django import template

register = template.Library()

##
# displays chi guadagna/perde boxes
##

@register.inclusion_tag("bilanci/_chi_guadagna_perde.html", takes_context=True)
def chi_guadagna_perde(context,**kwargs):
    return kwargs
