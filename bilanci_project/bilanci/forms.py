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

    text = forms.CharField(max_length=20, required=False)


class TerritoriComparisonSearchForm(forms.Form):

    cluster_territori = TerritoriClusterChoices(
        required=False,
        widget=TerritoriClusterChoices.widget(
            select2_options={
                'width': '20em',
                'placeholder': _(u"Cerca fra i Comuni"),
            }
        )
    )

    text = forms.CharField(max_length=20, required=False)