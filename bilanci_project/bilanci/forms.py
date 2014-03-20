from django import forms
from territori.fields import TerritoriChoices, TerritoriClusterChoices

from django.utils.translation import ugettext_lazy as _
from territori.models import Territorio


class TerritoriSearchForm(forms.Form):

    territori = TerritoriChoices(
        to_field_name = 'slug',
        required=False,
        label='',
        widget=TerritoriChoices.widget(
            select2_options={
                'width': '20em',
                'placeholder': _(u"CERCA UN COMUNE"),
            }
        )
    )



class TerritoriComparisonSearchForm(forms.Form):


    territorio_1 = TerritoriClusterChoices(
        to_field_name = 'slug',
        required=True,
        label='',
        widget=TerritoriClusterChoices.widget(
            select2_options={
                'containerCssClass': 'form-control',
                'width': '100%',
                'placeholder': _(u"UN COMUNE"),
            }
        )
    )

    territorio_2 = TerritoriClusterChoices(
        to_field_name = 'slug',
        required=True,
        label='',
        widget=TerritoriClusterChoices.widget(
            select2_options={
                'containerCssClass': 'form-control',
                'width': '100%',
                'placeholder': _(u"UN ALTRO COMUNE"),

            }
        )
    )
