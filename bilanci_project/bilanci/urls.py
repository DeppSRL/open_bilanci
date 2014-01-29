from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from bilanci.views import BilancioDetailView, TerritoriSearchRedirectView, ConfrontoView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='base.html'), name='home'),

    url(r'^territori/search', TerritoriSearchRedirectView.as_view()),
    url(r'^bilanci/(?P<slug>[-\w]+)$', BilancioDetailView.as_view(), name='bilanci-detail'),
    url(r'^confronto/', ConfrontoView.as_view(), name='confronto'),
    

    url(r'^select2/', include('django_select2.urls')),


    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
