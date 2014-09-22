__author__ = 'stefano'
from bilanci.views import BilancioOverView


class BilancioOverServicesView(BilancioOverView):
    def get_context_data(self, **kwargs ):

        context = super(BilancioOverServicesView, self).get_context_data(**kwargs)
        context['servizi_comuni'] = True
        return context
