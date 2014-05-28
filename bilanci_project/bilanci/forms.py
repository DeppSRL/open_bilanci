from django import forms
from territori.fields import TerritoriChoices, TerritoriClusterChoices, TerritoriChoicesClassifiche

from django.utils.translation import ugettext_lazy as _


class TerritoriSearchFormHome(forms.Form):

    territori = TerritoriChoices(
        to_field_name = 'slug',
        required=True,
        label='',
        widget=TerritoriChoices.widget(
            select2_options={
                'width': '48em',
                'placeholder': _(u"CERCA UN COMUNE, ENTRA NEI BILANCI, CONDIVIDI QUELLO CHE SCOPRI"),
                # 'allowClear': 'false',
            }
        )
    )

class TerritoriSearchFormClassifiche(forms.Form):

    territorio_id = TerritoriChoicesClassifiche(
        to_field_name = 'pk',
        required=True,
        label='',
        widget=TerritoriChoicesClassifiche.widget(
            select2_options={
                'width': '100%',
                'placeholder': _(u"CERCA UN COMUNE"),
            }
        )
    )
    selected_year = forms.MultiValueField(widget=forms.HiddenInput())
    selected_par_type = forms.MultiValueField(widget=forms.HiddenInput())
    selected_parameter = forms.MultiValueField(widget=forms.HiddenInput())
    selected_regioni = forms.MultiValueField(widget=forms.HiddenInput())
    selected_cluster = forms.MultiValueField(widget=forms.HiddenInput())


class TerritoriSearchForm(forms.Form):

    territori = TerritoriChoices(
        to_field_name = 'slug',
        required=True,
        label='',
        widget=TerritoriChoices.widget(
            select2_options={
                'width': '20em',
                'placeholder': _(u"CERCA UN COMUNE"),
                # 'allowClear': None,
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
