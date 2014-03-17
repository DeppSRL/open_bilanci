from django import forms
from territori.fields import TerritoriChoices, TerritoriClusterChoices

from django.utils.translation import ugettext_lazy as _
from territori.models import Territorio, Contesto


class TerritoriSearchForm(forms.Form):

    territori = TerritoriChoices(
        required=False, label='',
        widget=TerritoriChoices.widget(
            select2_options={
                'width': '20em',
                'placeholder': _(u"CERCA UN COMUNE"),
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
                'placeholder': _(u"CERCA UN COMUNE"),
            }
        )
    )


    def __init__(self,*args, **kwargs):

        # creates select box queryset excluding the Territorio which was selected as first parameter
        # ie. if Roma is selected, Roma won't appear in the select box
        # Territori are ordered based on name and on n. of inhabitants in 2012
        # self.base_fields['territorio_2'].queryset = \
        #     Territorio.objects.filter(territorio='C').exclude(pk=kwargs['initial']['territorio_1']).\
        #         order_by('-abitanti')

        self.base_fields['territorio_2'].queryset = \
            Contesto.objects.filter(anno=2012).filter(territorio__territorio='C').\
                exclude(territorio__pk=kwargs['initial']['territorio_1']).\
                order_by('territorio__denominazione','-istat_abitanti')

        super(TerritoriComparisonSearchForm, self).__init__(initial=kwargs['initial'])

