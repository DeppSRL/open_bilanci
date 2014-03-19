# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.inclusion_tag("bilanci/confronti_helpbox.html", takes_context=True)
def confronti_helpbox(context, territorio):
    return {'territorio': territorio}