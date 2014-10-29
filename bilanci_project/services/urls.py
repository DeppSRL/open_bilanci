__author__ = 'stefano'
from bilanci.views import BilancioNotFoundView, BilancioRedirectView, BilancioOverView, BilancioDettaglioView, BilancioComposizioneView, BilancioIndicatoriView, \
    IncarichiVoceJSONView, IncarichiIndicatoriJSONView, CompositionWidgetView

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = patterns('',

    url(r'^$', BilancioOverView.as_view(), name='bilanci-overview-services'),

    url(r'^(?P<section>[-\w]+)/composizione$', BilancioComposizioneView.as_view(), name='bilanci-composizione-services'),
    url(r'^(?P<section>[-\w]+)/dettaglio$', BilancioDettaglioView.as_view(), name='bilanci-dettaglio-services'),
    #
    url(r'^indicatori$', BilancioIndicatoriView.as_view(), name='bilanci-indicatori-services'),

    # url(r'^bilancio-not-found$', BilancioNotFoundView.as_view(), name='bilancio-not-found-services'),


) + static(settings.OPENDATA_URL, document_root=settings.OPENDATA_ROOT)

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
