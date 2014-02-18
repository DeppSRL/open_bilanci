from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from bilanci.views import ConfrontoView, BilancioRedirectView, \
    BilancioSpeseView, BilancioIndicatoriView, BilancioEntrateView, BilancioView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),

    url(r'^bilanci/search', BilancioRedirectView.as_view()),
    url(r'^bilanci/(?P<slug>[-\w]+)/entrate', BilancioEntrateView.as_view(), name='bilanci-entrate'),
    url(r'^bilanci/(?P<slug>[-\w]+)/spese', BilancioSpeseView.as_view(), name='bilanci-spese'),
    url(r'^bilanci/(?P<slug>[-\w]+)/indicatori', BilancioIndicatoriView.as_view(), name='bilanci-indicatori'),

    url(r'^bilanci/(?P<slug>[-\w]+)', BilancioView.as_view(), name='bilanci-overall'),

    url(r'^confronto/(?P<slugA>[-\w]+)/(?P<slugB>[-\w]+)', ConfrontoView.as_view(), name='confronto'),

    url(r'^pages/', TemplateView.as_view(template_name='static_page.html'), name='static_page'),

    url(r'^page-not-found$', TemplateView.as_view(template_name='404.html'), name='404'),

    url(r'^select2/', include('django_select2.urls')),

    url(r'^front-edit/', include('front.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
