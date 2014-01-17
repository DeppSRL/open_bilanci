from pprint import pprint
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView, RedirectView
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
        return context



class TerritoriSearchRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        territorio = get_object_or_404(Territorio, pk=int(self.request.GET.get('territori',0)))

        return reverse('bilanci-detail', args=(territorio.slug,))
