from pprint import pprint
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView
from bilanci.forms import TerritoriComparisonSearchForm
from territori.models import Territorio

class HomeView(TemplateView):
    template_name = "home.html"


class BilancioDetailView(DetailView):
    model = Territorio
    context_object_name = "territorio"
    template_name = 'bilancio.html'

    def get_context_data(self, **kwargs ):
        territorio = self.get_object()
        context = super(BilancioDetailView, self).get_context_data(**kwargs)
        context['territori_comparison_search_form'] = TerritoriComparisonSearchForm(
            initial={'territorio_1':territorio.pk}
            )
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