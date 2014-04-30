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

class EarlyBirdForm(forms.Form):
    my_default_errors = {
        'required': 'Campo richiesto',
        'invalid': 'Attenzione: il valore inserito non &egrave; valido',

    }

    nome = forms.CharField(max_length=200, error_messages=my_default_errors, required=True)
    cognome = forms.CharField(max_length=200, error_messages=my_default_errors, required=True)
    email = forms.EmailField(max_length=200, error_messages=my_default_errors, required=True)
