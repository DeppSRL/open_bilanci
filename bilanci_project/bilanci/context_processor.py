__author__ = 'stefano'
from django.conf import settings
from django.contrib.sites.models import get_current_site
from .forms import TerritoriSearchForm, TerritoriComparisonSearchForm

def main_settings(request):
    """
    Default context processor for openaction.
    """
    return {
        'site': get_current_site(request),
        'territori_search_form': TerritoriSearchForm(request.GET),
        'settings': {
            'DEBUG': settings.DEBUG,
            'TEMPLATE_DEBUG': settings.TEMPLATE_DEBUG,
        }
    }