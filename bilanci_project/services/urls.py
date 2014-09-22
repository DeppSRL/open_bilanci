__author__ = 'stefano'
# from bilanci.views import BilancioNotFoundView, BilancioRedirectView, BilancioOverView, BilancioDettaglioView, BilancioComposizioneView, BilancioIndicatoriView, \
#     IncarichiVoceJSONView, IncarichiIndicatoriJSONView, BilancioCompositionWidgetView
from .views import BilancioOverServicesView, BilancioIndicatoriServicesView
    # BilancioComposizioneServicesView, BilancioDettaglioServicesView,
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = patterns('',

    url(r'^$', BilancioOverServicesView.as_view(), name='bilanci-overview-services'),

    # url(r'^(?P<section>[-\w]+)/composizione$', BilancioComposizioneServicesView.as_view(), name='bilanci-composizione-services'),
    # url(r'^(?P<section>[-\w]+)/dettaglio$', BilancioDettaglioServicesView.as_view(), name='bilanci-dettaglio-services'),
    #
    url(r'^indicatori$', BilancioIndicatoriServicesView.as_view(), name='bilanci-indicatori-services'),

    # url(r'^bilancio-not-found$', BilancioNotFoundView.as_view(), name='bilancio-not-found-services'),

    # Json view for linegraph voci di bilancio
    # url(r'^incarichi_voce/(?P<territorio_opid>[-\w]+)/(?P<voce_slug>[-\w]+)', IncarichiVoceJSONView.as_view(), name = "incarichi-voce-json"),
    #
    # # Json view for linegraph indicatori
    # url(r'^incarichi_indicatori/(?P<territorio_opid>[-\w]+)', IncarichiIndicatoriJSONView.as_view(), name = "incarichi-indicatori-json"),

    # # Composition widget for Bilancio overview / entrate / spese
    # url(r'^composition_widget/(?P<widget_type>[-\w]+)/(?P<territorio_slug>[-\w]+)/(?P<bilancio_year>[-\d]{4})/(?P<bilancio_type>[-\w]+)/',
    #     BilancioCompositionWidgetView.as_view(), name = "composition-widget"),


) + static(settings.OPENDATA_URL, document_root=settings.OPENDATA_ROOT)

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
