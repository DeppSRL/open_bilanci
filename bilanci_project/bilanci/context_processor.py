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
        # sets start / end for timeline graph
        'timeline_start_year': settings.TIMELINE_START_DATE.year,
        'timeline_end_year': settings.TIMELINE_END_DATE.year,
        'settings': {
            'DEBUG': settings.DEBUG,
            'TEMPLATE_DEBUG': settings.TEMPLATE_DEBUG,
        },
        'site_full_url': request.build_absolute_uri('/')[:-1],
        'page_full_url': request.build_absolute_uri(),
    }