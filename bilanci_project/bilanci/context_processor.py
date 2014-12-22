__author__ = 'stefano'
from django.conf import settings
from django.contrib.sites.models import get_current_site
from .forms import TerritoriSearchForm


def main_settings(request):
    """
    Default context processor for openaction.
    """
    return {
        'site': get_current_site(request),
        'instance_type': settings.INSTANCE_TYPE,
        'territori_search_form': TerritoriSearchForm(),
        # sets start / end for timeline graph
        'timeline_start_year': settings.APP_START_YEAR,
        'timeline_end_year': settings.APP_END_YEAR,
        'classifiche_allowed_years': [str(x) for x in range(settings.CLASSIFICHE_START_YEAR, settings.CLASSIFICHE_END_YEAR+1)],
        'settings': {
            'DEBUG': settings.DEBUG,
            'TEMPLATE_DEBUG': settings.TEMPLATE_DEBUG,
            'SITE_VERSION': settings.SITE_VERSION,
        },
        'site_full_url': request.build_absolute_uri('/')[:-1],
        'page_full_url': request.build_absolute_uri(),
    }