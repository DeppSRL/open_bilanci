import re
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import resolve
from bilanci.views import HomeTemporaryView, PageNotFoundTemplateView, BilancioDettaglioView, BilancioNotFoundView, \
    BilancioIndicatoriView, BilancioComposizioneView, CompositionWidgetView
from services import urls

from services.models import PaginaComune


class PrivateBetaMiddleware(object):
    """
    Add this to your ``MIDDLEWARE_CLASSES`` make all views except for
    those in the account application require that a user be logged in.
    This can be a quick and easy way to restrict views on your site,
    particularly if you remove the ability to create accounts.
    **Settings:**
    ``EARLYBIRD_ENABLE``
    Whether or not the beta middleware should be used. If set to `False`
    the PrivateBetaMiddleware middleware will be ignored and the request
    will be returned. This is useful if you want to disable early bird
    on a development machine. Default is `True`.
    """

    def __init__(self):
        self.enable_beta = settings.EARLYBIRD_ENABLE

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated() or not self.enable_beta:
            # User is logged in, no need to check anything else.
            return

        whitelisted_modules = ['django.contrib.auth.views', 'django.views.static', 'django.contrib.admin.sites']
        if '%s' % view_func.__module__ in whitelisted_modules:
            return
        else:
            return HomeTemporaryView.as_view()(request)


class ComuniServicesMiddleware(object):

    """
    ComuniServicesMiddleware serves to enable the Servizi ai Comuni.
    The request is filtered by the http_host: if the host belongs to a Comune
    that has activated the services then the special template is shown for
    Dettaglio, Composizione e Indicatori views.

    If the request comes from the production / staging host then no action is taken.

    In all other cases a 404 page is shown
    """

    def process_request(self, request):

        request.servizi_comuni = False
         # http_host gets the http_host string removing the eventual port number
        regex = re.compile("^([\w\.]+):?.*")
        http_host = regex.findall(request.META['HTTP_HOST'])[0]

        if http_host in settings.HOSTS_COMUNI:

            try:
                pagina_comune = PaginaComune.objects.get(
                    host=http_host,
                    active=True
                )
            except ObjectDoesNotExist:
                return PageNotFoundTemplateView.as_view()(request)

            else:

                # depending on the request.path resolves the url with bilanci.urls or services.urls
                # paths coming from the widget, the json views and the static files are resolved with bilanci.urls
                items = ['composition_widget', 'incarichi_indicatori', 'incarichi_voce', '/static/', 'comune_logo' ]

                def isin(x): return x in request.path

                try:
                    map(isin, items).index(True)
                except ValueError:

                    # redirects to Bilanci Servizi view injecting the territorio slug in the kwargs
                    view, args, kwargs = resolve(path=request.path, urlconf=urls)

                    kwargs['slug'] = pagina_comune.territorio.slug
                    request.servizi_comuni = True

                    return view(request, args, **kwargs)

                else:
                    return

        return
