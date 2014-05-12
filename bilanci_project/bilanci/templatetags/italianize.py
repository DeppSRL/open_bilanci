# -*- coding: utf-8 -*-

'''
this template filter transforms cypher numbers in the Italian format for money:
 ex. 91.234.333,22 (for Euro)
'''



from django import template
from decimal import *
from bilanci.utils.moneydate import moneyfmt

register = template.Library()

@register.filter(name='italianize')
def italianize(value):
    decimal_value = Decimal(format(value, ".15g"))
    return moneyfmt(decimal_value,2,"",".",",")