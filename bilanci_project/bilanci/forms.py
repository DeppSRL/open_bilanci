from django import forms
from territori.fields import TerritoriChoices, TerritoriClusterChoices

from django.utils.translation import ugettext_lazy as _
from territori.models import Territorio


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


    def __init__(self,*args, **kwargs):

        # crea il queryset della select box escludendo il Comune che e' il primo argomento del confronto
        # ad es. se sono sulla pagina di Roma nella select box non dovra' comparire Roma
        self.base_fields['territorio_2'].queryset = \
            Territorio.objects.filter(territorio='C').exclude(pk=kwargs['initial']['territorio_1']).\
                order_by('-abitanti')
        super(TerritoriComparisonSearchForm, self).__init__(initial=kwargs['initial'])

