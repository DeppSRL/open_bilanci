from django import forms
from territori.fields import TerritoriChoices, TerritoriClusterChoices

from django.utils.translation import ugettext_lazy as _


class TerritoriSearchForm(forms.Form):

    territori = TerritoriChoices(
        required=False,
        widget=TerritoriChoices.widget(
            select2_options={
                'width': '20em',
                'placeholder': _(u"Cerca fra i Comuni"),
            }
        )
    )



class TerritoriComparisonSearchForm(forms.Form):

    territorio_1 = forms.CharField(widget=forms.HiddenInput())

    territorio_2 = TerritoriClusterChoices(
        required=False,
        widget=TerritoriClusterChoices.widget(
            select2_options={
                'width': '20em',
                'placeholder': _(u"Cerca fra i Comuni"),
            }
        )
    )


