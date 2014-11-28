from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .sitemap import sitemaps

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from bilanci.views import BilancioRedirectView, \
    BilancioIndicatoriView, BilancioComposizioneView, BilancioDettaglioView, BilancioOverView, IncarichiVoceJSONView,\
    IncarichiIndicatoriJSONView, HomeView, ConfrontiHomeView, ConfrontiEntrateView, ConfrontiSpeseFunzioniView,\
    ConfrontiSpeseInterventiView, ConfrontiIndicatoriView, ConfrontiRedirectView, ConfrontiDataJSONView,\
    ClassificheRedirectView, ClassificheListView, CompositionWidgetView, BilancioNotFoundView,\
    ClassificheSearchView, MappeTemplateView, PageNotFoundTemplateView, StaticPageView, TerritorioNotFoundView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^robots\.txt$', include('robots.urls')),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login', ),
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login', name='logout', ),

    url(r'^mappe$', MappeTemplateView.as_view(), name='mappe'),
    url(r'^bilancio-not-found$', BilancioNotFoundView.as_view(), name='bilancio-not-found'),
    url(r'^territorio-not-found$', TerritorioNotFoundView.as_view(), name='territorio-not-found'),
    url(r'^bilanci/search', BilancioRedirectView.as_view(), name='bilanci-search'),
    url(r'^bilanci/(?P<slug>[-\w]+)$', BilancioOverView.as_view(), name='bilanci-overview'),
    url(r'^bilanci/(?P<slug>[-\w]+)/(?P<section>[-\w]+)/composizione$', BilancioComposizioneView.as_view(), name='bilanci-composizione'),
    url(r'^bilanci/(?P<slug>[-\w]+)/(?P<section>[-\w]+)/dettaglio$', BilancioDettaglioView.as_view(), name='bilanci-dettaglio'),

    url(r'^bilanci/(?P<slug>[-\w]+)/indicatori$', BilancioIndicatoriView.as_view(), name='bilanci-indicatori'),

    # Json view for linegraph voci di bilancio
    url(r'^incarichi_voce/(?P<territorio_opid>[-\w]+)/(?P<voce_slug>[-\w]+)', IncarichiVoceJSONView.as_view(), name = "incarichi-voce-json"),

    # Json view for linegraph indicatori
    url(r'^incarichi_indicatori/(?P<territorio_opid>[-\w]+)', IncarichiIndicatoriJSONView.as_view(), name = "incarichi-indicatori-json"),

    # Composition widget for Bilancio overview / entrate / spese
    url(r'^composition_widget/(?P<widget_type>[-\w]+)/(?P<territorio_slug>[-\w]+)/(?P<bilancio_year>[-\d]{4})/(?P<bilancio_type>[-\w]+)/',
        CompositionWidgetView.as_view(), name = "composition-widget"),

    # classifiche
    url(r'^classifiche/$', ClassificheRedirectView.as_view(), name='classifiche-redirect'),
    url(r'^classifiche/(?P<parameter_type>[-\w]+)/(?P<parameter_slug>[-\w]+)/(?P<anno>[-\d]{4})$', ClassificheListView.as_view(), name='classifiche-list'),
    url(r'^classifiche/search', ClassificheSearchView.as_view(), name='classifiche-search'),

    # confronti
    url(r'^confronti/$', ConfrontiHomeView.as_view(), name='confronti-home'),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)$',
        ConfrontiRedirectView.as_view(), name='confronti-redirect'
        ),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)/entrate/(?P<parameter_slug>[-\w]+)',
        ConfrontiEntrateView.as_view(), name='confronti-entrate'
        ),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)/spese-funzioni/(?P<parameter_slug>[-\w]+)',
        ConfrontiSpeseFunzioniView.as_view(), name='confronti-spese-funzioni'
        ),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)/spese-interventi/(?P<parameter_slug>[-\w]+)',
        ConfrontiSpeseInterventiView.as_view(), name='confronti-spese-interventi'
        ),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)/indicatori/(?P<parameter_slug>[-\w]+)',
        ConfrontiIndicatoriView.as_view(), name='confronti-indicatori'
        ),

    url(r'^confronti_data/(?P<territorio_1_opid>[-\w]+)/(?P<territorio_2_opid>[-\w]+)/(?P<parameter_type>[-\w]+)/(?P<parameter_slug>[-\w]+)$',
        ConfrontiDataJSONView.as_view(), name = "confronti-data-json"
        ),


    # url(r'^pages/', TemplateView.as_view(template_name='static_page.html'), name='static_page'),
    url(r'^pages/', StaticPageView.as_view(), name='static_page'),

    url(r'^page-not-found$', PageNotFoundTemplateView.as_view(), name='404'),

    url(r'^select2/', include('django_select2.urls')),

    url(r'^front-edit/', include('front.urls')),

    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
) + static(settings.OPENDATA_URL, document_root=settings.OPENDATA_ROOT)


# Sitemap: disabled in staging
if settings.INSTANCE_TYPE != 'staging':

    urlpatterns += patterns('django.contrib.sitemaps.views',
        (r'^sitemap\.xml$', 'index', {'sitemaps': sitemaps}),
        (r'^sitemap-(?P<section>.+)\.xml$', 'sitemap', {'sitemaps': sitemaps}),
    )

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
