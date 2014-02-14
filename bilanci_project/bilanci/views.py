from django.core.cache import cache
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView

from bilanci.forms import TerritoriComparisonSearchForm
from bilanci.utils import couch

from territori.models import Territorio

class HomeView(TemplateView):
    template_name = "home.html"


class BilancioRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        territorio = get_object_or_404(Territorio, pk=int(self.request.GET.get('territori',0)))

        couch_data = couch.get(territorio.cod_finloc)

        # last year with data
        if couch_data:

            # put in new values via regular dict
            year =  sorted(couch_data.keys())[-3]
            tipo_bilancio = "consuntivo"
            if couch_data[year][tipo_bilancio] == {}:
                tipo_bilancio = "preventivo"
            kwargs.update({'slug': territorio.slug})
            try:
                url = reverse('bilanci-detail', args=args , kwargs=kwargs)
            except NoReverseMatch:
                return reverse('404')

            return url + '?year=' + year +"&type=" + tipo_bilancio
        else:
            return reverse('404')

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
        couch_data = couch.get(territorio.cod_finloc)

        context['year'] = self.request.GET['year']
        context['bilanci'] = couch_data
        context['tipo_bilancio'] = self.request.GET['type']

        return context


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