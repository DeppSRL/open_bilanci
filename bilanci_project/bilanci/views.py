import time
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView, View
import requests
import json
from bilanci.models import ValoreBilancio, Voce
from django.http.response import HttpResponse
from bilanci.utils import couch
from collections import OrderedDict

from territori.models import Territorio, Contesto

class HomeView(TemplateView):
    template_name = "home.html"


class InstitutionalChargesJSONView(View):

    def get(self, request, **kwargs):
        response = None

        territorio = get_object_or_404(Territorio, op_id =int(kwargs['territorioOpId']))
        # get politicians data for Territorio
        sindaci_results = requests.get(
            "http://api3.staging.deppsviluppo.org/politici/instcharges?charge_type_id=14&location_id={0}&order_by=date".\
                format(territorio.op_id)
            ).json()['results']


        time_spans = []
        date_fmt = '%Y-%m-%d'
        timeline_start = time.strptime("2003-01-01", date_fmt)
        timeline_end = time.strptime("2012-12-31", date_fmt)


        for sindaco in sindaci_results:

            incarico_start = time.strptime(sindaco['date_start'], date_fmt)
            incarico_end = None
            if sindaco['date_end']:
                incarico_end = time.strptime(sindaco['date_end'],date_fmt)

            # considers only charges which are contained between timeline_start / end
            if (incarico_end is None or incarico_end > timeline_start) and incarico_start < timeline_end:

                if incarico_end is None or incarico_end > timeline_end:
                    incarico_end = timeline_end

                if incarico_start < timeline_start:
                    incarico_start = timeline_start



                dict_visup = {
                    'start':  time.strftime(date_fmt, incarico_start),
                    'end': time.strftime(date_fmt,incarico_end),
                    'icon': sindaco['politician']['image_uri'],
                    'label': "{0}.{1}".format(sindaco['politician']['first_name'][0],sindaco['politician']['last_name'],),
                    'sublabel': sindaco['party']['acronym'],
                    'color': "#ff0000",
                    'highlightColor': "#00ff00"
                }
                time_spans.append(dict_visup)




        # return HttpResponse(content=json.dumps(sindaci_results), content_type="application/json")
        return HttpResponse(content=json.dumps({"timeSpans":[time_spans], 'data':[], 'legend':[] } ), content_type="application/json")



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
                url = reverse('bilanci-overall', args=args , kwargs=kwargs)
            except NoReverseMatch:
                return reverse('404')

            return url + '?year=' + year +"&type=" + tipo_bilancio
        else:
            return reverse('404')

class BilancioView(DetailView):
    model = Territorio
    context_object_name = "territorio"
    template_name = 'bilanci/bilancio.html'

    def get_context_data(self, **kwargs ):

        context = super(BilancioView, self).get_context_data(**kwargs)
        territorio = self.get_object()
        query_string = self.request.META['QUERY_STRING']

        year = self.request.GET['year']
        tipo_bilancio = self.request.GET['type']
        menu_voices_kwargs = {'slug': territorio.slug}

        # get Comune context data from db
        context['comune_context'] = Contesto.get_context(year, territorio)
        context['slug'] = territorio.slug
        context['query_string'] = query_string
        context['year'] = year
        context['tipo_bilancio'] = tipo_bilancio
        context['menu_voices'] = OrderedDict([
            ('bilancio', reverse('bilanci-overall', kwargs=menu_voices_kwargs)),
            ('entrate', reverse('bilanci-entrate', kwargs=menu_voices_kwargs)),
            ('spese', reverse('bilanci-spese', kwargs=menu_voices_kwargs)),
            ('indicatori', reverse('bilanci-indicatori', kwargs=menu_voices_kwargs))
        ])

        return context


class BilancioDetailView(BilancioView):

    def get_context_data(self, **kwargs ):

        context = super(BilancioDetailView, self).get_context_data(**kwargs)
        territorio = self.get_object()
        query_string = self.request.META['QUERY_STRING']
        year = self.request.GET['year']

        tipo_bilancio = self.request.GET['type']
        voce_slug = self.get_slug()

        # gets the tree structure from db
        bilancio_rootnode = Voce.objects.get(slug = voce_slug)

        # gets the part of bilancio data which is referring to Voce nodes which are
        # descendants of bilancio_treenodes to minimize queries and data size
        bilancio_valori = ValoreBilancio.objects.filter(territorio = territorio, anno=year).\
            filter(voce__in=bilancio_rootnode.get_descendants(include_self=True).values_list('pk', flat=True))

        menu_voices_kwargs = {'slug': territorio.slug}

        context['bilancio_valori'] = bilancio_valori
        context['bilancio_rootnode'] = bilancio_rootnode
        context['bilancio_tree'] =  bilancio_rootnode.get_descendants(include_self=True)
        context['slug'] = territorio.slug
        context['territorio_opid'] = territorio.op_id
        context['query_string'] = query_string
        context['year'] = year
        context['tipo_bilancio'] = tipo_bilancio
        context['menu_voices'] = OrderedDict([
            ('bilancio', reverse('bilanci-overall', kwargs=menu_voices_kwargs)),
            ('entrate', reverse('bilanci-entrate', kwargs=menu_voices_kwargs)),
            ('spese', reverse('bilanci-spese', kwargs=menu_voices_kwargs)),
            ('indicatori', reverse('bilanci-indicatori', kwargs=menu_voices_kwargs))
        ])
        return context



class BilancioEntrateView(BilancioDetailView):
    template_name = 'bilanci/entrate.html'

    def get_slug(self):
        return "{0}-{1}".format(self.request.GET['type'],"entrate")



class BilancioSpeseView(BilancioDetailView):
    template_name = 'bilanci/spese.html'

    def get_slug(self):
        return "{0}-{1}".format(self.request.GET['type'],"spese")




class BilancioIndicatoriView(BilancioView):
    template_name = 'bilanci/indicatori.html'


class ConfrontoView(TemplateView):
    template_name = "bilanci/confronto.html"

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