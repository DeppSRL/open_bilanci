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


class IncarichiGetterMixin(object):
    
    date_fmt = '%Y-%m-%d'
    
    def transform_incarichi(self, incarichi, timeline_start, timeline_end, is_commissari):

        incarichi_transformed = []
        for incarico in incarichi:

            incarico_start = time.strptime(incarico['date_start'], self.date_fmt)
            incarico_end = None
            if incarico['date_end']:
                incarico_end = time.strptime(incarico['date_end'],self.date_fmt)

            # considers only charges which are contained between timeline_start / end
            if (incarico_end is None or incarico_end > timeline_start) and incarico_start < timeline_end:

                if incarico_end is None or incarico_end > timeline_end:
                    incarico_end = timeline_end

                if incarico_start < timeline_start:
                    incarico_start = timeline_start

                dict_widget = {
                    'start':  time.strftime(self.date_fmt, incarico_start),
                    'end': time.strftime(self.date_fmt,incarico_end),
                    'label': "{0}.{1}".\
                        format(
                            incarico['politician']['first_name'][0].upper(),
                            incarico['politician']['last_name'].title().encode('utf-8'),
                        ),

                    # todo: move colors in settings
                    'color': "#5e6a77",
                    'highlightColor': "#cc6633",
                }

                if is_commissari:
                    # todo: add dummy image for commissario
                    # todo: aggiungere motivo commissariamento
                    dict_widget['icon'] = ''
                    dict_widget['sublabel'] = 'Commissario'
                else:
                    # todo: add dummy image if sindaco doesn't have a pic
                    dict_widget['icon'] = incarico['politician']['image_uri']
                    dict_widget['sublabel'] = incarico['party']['acronym']

                incarichi_transformed.append(dict_widget)

        return incarichi_transformed

    def get_incarichi_api(self, territorio_opid, incarico_type):
        api_results_json = requests.get(
            "http://api3.openpolis.it/politici/instcharges?charge_type_id={0}&location_id={1}&order_by=date".\
                format(incarico_type, territorio_opid)
            ).json()

        if 'results' in api_results_json:
            return api_results_json['results']
        else:
            return None


    def get_incarichi(self, territorio_opid, timeline_start, timeline_end):

        # get sindaci
        sindaci_api = self.get_incarichi_api(territorio_opid, incarico_type='14')
        # transform data format to fit Visup widget specifications
        sindaci_transformed = self.transform_incarichi(sindaci_api, timeline_start, timeline_end, is_commissari=False)

        # get commissari
        commissari_api = self.get_incarichi_api(territorio_opid, incarico_type='16')
        # transform data format to fit Visup widget specifications
        commissari_transformed = self.transform_incarichi(commissari_api, timeline_start, timeline_end, is_commissari=True)

        # adds up sindaci and commissari
        incarichi = sindaci_transformed
        incarichi.extend(commissari_transformed)

        return incarichi


    ##
    # transform bilancio values to be feeded to Visup widget
    ##
    def transform_voce(self, voce_values):

        series_dict = {
            'id':1,
            'color': "#ff0000",
            'series':[]
        }

        for voce_value in voce_values:
            series_dict['series'].append(
                [voce_value.anno, voce_value.valore]
            )

        return series_dict

    ##
    # get bilancio values of specified voce for Territorio in the time span
    ##

    def get_voce(self, territorio, voce_bilancio, timeline_start_year, timeline_end_year):

        voce_values = ValoreBilancio.objects.filter(
            territorio = territorio,
            voce = voce_bilancio,
            anno__gte = timeline_start_year,
            anno__lte = timeline_end_year
        ).order_by('anno')

        return self.transform_voce(voce_values)


class IncarichiVoceJSONView(View, IncarichiGetterMixin):
    def get(self, request, **kwargs):

        # get territorio_opid from GET parameter
        territorio_opid = kwargs['territorio_opid']
        territorio = get_object_or_404(Territorio, op_id = territorio_opid)
        # get voce bilancio from GET parameter
        voce_slug = kwargs['voce_slug']
        if voce_slug:
            voce_bilancio = get_object_or_404(Voce, slug = voce_slug)
        else:
            return

        #     sets the start / end of sindaci timeline
        # todo: make timeline start / end dynamic
        timeline_start = time.strptime("2003-01-01", self.date_fmt)
        timeline_end = time.strptime("2012-12-31", self.date_fmt)

        incarichi_set = self.get_incarichi(territorio_opid, timeline_start=timeline_start, timeline_end= timeline_end)

        # gets voce value for the territorio over the period set
        voce_set = self.get_voce(territorio, voce_bilancio , timeline_start.tm_year, timeline_end.tm_year)


        return HttpResponse(
            content=json.dumps(
                {
                    "timeSpans":[incarichi_set],
                    'data':[voce_set],
                    'legend':[]
                }
            ),
            content_type="application/json"
        )


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
        context['territorio_opid'] = territorio.op_id
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