from django import forms
from territori.fields import TerritoriChoices

from django.utils.translation import ugettext_lazy as _


class TerritoriSearchForm(forms.Form):

    territori = TerritoriChoices(
        required=False,
        widget=TerritoriChoices.widget(
            select2_options={
                'width': '20em',
                'placeholder': _(u"Search location"),
            }
        )
    )

    text = forms.CharField(max_length=20, required=False)

