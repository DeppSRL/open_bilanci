from pprint import pprint
import couchdb
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView
from bilanci.forms import TerritoriComparisonSearchForm
from bilanci.utils.comuni import FLMapper
from bilanci.utils import couch

from territori.models import Territorio

class HomeView(TemplateView):
    template_name = "home.html"


class BilancioRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        territorio = Territorio.objects.get(slug=kwargs['slug'])

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        city = mapper.get_city(territorio.cod_finloc)
        couch_data = couch.get(city)

        # last year with data
        kwargs.update({'year': sorted(couch_data.keys())[-3]})

        try:
            url = reverse('bilanci-detail-year', args=args, kwargs=kwargs)
        except NoReverseMatch:
            return None

        return url

class BilancioDetailView(DetailView):
    model = Territorio
    context_object_name = "territorio"
    template_name = 'bilanci/bilancio.html'

    def get_context_data(self, **kwargs ):

        territorio = self.get_object()
        context = super(BilancioDetailView, self).get_context_data(**kwargs)
        context['territori_comparison_search_form'] = TerritoriComparisonSearchForm(
            initial={'territorio_1':territorio.pk}
            )

        # get the couchdb doc
        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        city = mapper.get_city(territorio.cod_finloc)
        couch_data = couch.get(city)

        context['year'] = self.kwargs['year']
        context['bilanci'] = couch_data

        return context



class TerritoriSearchRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        territorio = get_object_or_404(Territorio, pk=int(self.request.GET.get('territori',0)))

        return reverse('bilanci-detail', args=(territorio.slug,))


class ConfrontoView(TemplateView):
    template_name = "confronto.html"

    def get_context_data(self, **kwargs):

        context = {}
        territorio_1_pk = int(self.request.GET.get('territorio_1',0))
        territorio_2_pk = int(self.request.GET.get('territorio_2',0))

        if territorio_1_pk == territorio_2_pk:
            return redirect('home')


        territorio_1 = get_object_or_404(Territorio, pk=territorio_1_pk)
        territorio_2 = get_object_or_404(Territorio, pk=territorio_2_pk)


        context['territorio_1'] = territorio_1
        context['territorio_2'] = territorio_2
        return context