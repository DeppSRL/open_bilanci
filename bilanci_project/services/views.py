__author__ = 'stefano'
from bilanci.views import BilancioOverView, BilancioIndicatoriView

class InjectVariable(object):
    def get_context_data(self, **kwargs ):

        context = super(InjectVariable, self).get_context_data(**kwargs)
        context['servizi_comuni'] = True
        return context


class BilancioOverServicesView(BilancioOverView, InjectVariable):
    pass


class BilancioIndicatoriServicesView(BilancioIndicatoriView, InjectVariable):
    pass
