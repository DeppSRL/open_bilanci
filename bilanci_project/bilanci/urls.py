from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from bilanci.views import BilancioRedirectView, \
    BilancioSpeseView, BilancioIndicatoriView, BilancioEntrateView, BilancioOverView, IncarichiVoceJSONView, IncarichiIndicatoriJSONView,\
    HomeView, ConfrontiHomeView, ConfrontiEntrateView, ConfrontiSpeseView, ConfrontiIndicatoriView, ConfrontiRedirectView,\
    ConfrontiDataJSONView, ClassificheRedirectView, ClassificheListView, BilancioCompositionWidgetView, HomeTemporaryView, BilancioNotFoundView, HomeReleaseView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', HomeTemporaryView.as_view(), name='home-temporary'),
    url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login', ),
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login', name='logout', ),
    url(r'^home$', HomeView.as_view(), name='home'),

    url(r'^bilancio-not-found$', BilancioNotFoundView.as_view(), name='bilancio-not-found'),
    url(r'^bilanci/search', BilancioRedirectView.as_view(), name='bilanci-search'),
    url(r'^bilanci/(?P<slug>[-\w]+)$', BilancioOverView.as_view(), name='bilanci-overview'),
    url(r'^bilanci/(?P<slug>[-\w]+)/entrate$', BilancioEntrateView.as_view(), name='bilanci-entrate'),
    url(r'^bilanci/(?P<slug>[-\w]+)/spese$', BilancioSpeseView.as_view(), name='bilanci-spese'),
    url(r'^bilanci/(?P<slug>[-\w]+)/indicatori$', BilancioIndicatoriView.as_view(), name='bilanci-indicatori'),

    # Json view for linegraph voci di bilancio
    url(r'^incarichi_voce/(?P<territorio_opid>[-\w]+)/(?P<voce_slug>[-\w]+)', IncarichiVoceJSONView.as_view(), name = "incarichi-voce-json"),

    # Json view for linegraph indicatori
    url(r'^incarichi_indicatori/(?P<territorio_opid>[-\w]+)', IncarichiIndicatoriJSONView.as_view(), name = "incarichi-indicatori-json"),

    # Composition widget for Bilancio overview / entrate / spese
    url(r'^composition_widget/(?P<widget_type>[-\w]+)/(?P<territorio_slug>[-\w]+)/(?P<bilancio_year>[-\d]{4})/(?P<bilancio_type>[-\w]+)/',
        BilancioCompositionWidgetView.as_view(), name = "composition-widget"),

    # classifiche
    url(r'^classifiche$', ClassificheRedirectView.as_view(), name='classifiche-redirect'),
    url(r'^classifiche/(?P<parameter_type>[-\w]+)/(?P<parameter_slug>[-\w]+)/(?P<anno>[-\d]{4})$', ClassificheListView.as_view(), name='classifiche-list'),

    # confronti
    url(r'^confronti$', ConfrontiHomeView.as_view(), name='confronti-home'),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)$',
        ConfrontiRedirectView.as_view(), name='confronti-redirect'
        ),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)/entrate/(?P<parameter_slug>[-\w]+)$',
        ConfrontiEntrateView.as_view(), name='confronti-entrate'
        ),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)/spese/(?P<parameter_slug>[-\w]+)$',
        ConfrontiSpeseView.as_view(), name='confronti-spese'
        ),

    url(r'^confronti/(?P<territorio_1_slug>[-\w]+)/(?P<territorio_2_slug>[-\w]+)/indicatori/(?P<parameter_slug>[-\w]+)$',
        ConfrontiIndicatoriView.as_view(), name='confronti-indicatori'
        ),

    url(r'^confronti_data/(?P<territorio_1_opid>[-\w]+)/(?P<territorio_2_opid>[-\w]+)/(?P<parameter_type>[-\w]+)/(?P<parameter_slug>[-\w]+)$',
        ConfrontiDataJSONView.as_view(), name = "confronti-data-json"
        ),


    url(r'^pages/', TemplateView.as_view(template_name='static_page.html'), name='static_page'),

    url(r'^page-not-found$', TemplateView.as_view(template_name='404.html'), name='404'),

    url(r'^select2/', include('django_select2.urls')),

    url(r'^front-edit/', include('front.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
) + static(settings.OPENDATA_URL, document_root=settings.OPENDATA_ROOT)
