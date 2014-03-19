import re
import time
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView, View
import requests
import json
from bilanci.forms import TerritoriComparisonSearchForm
from bilanci.models import ValoreBilancio, Voce, Indicatore
from django.http.response import HttpResponse, HttpResponseRedirect
from bilanci.utils import couch
from collections import OrderedDict
from django.conf import settings

from territori.models import Territorio, Contesto

class HomeView(TemplateView):
    template_name = "home.html"


class IncarichiGetterMixin(object):
    
    date_fmt = '%Y-%m-%d'
            
    #     sets the start / end of graphs 
    timeline_start = settings.GRAPH_START_DATE
    timeline_end = settings.GRAPH_END_DATE
    
    def transform_incarichi(self, incarichi):

        incarichi_transformed = []
        for incarico in incarichi:

            incarico_start = incarico['date_start']
            incarico_end = None
            if incarico['date_end']:
                incarico_end = incarico['date_end']


            dict_widget = {
                'start':  time.strftime(self.date_fmt, incarico_start),
                'end': time.strftime(self.date_fmt,incarico_end),

                # sets incarico marker color and highlight
                'color': settings.SINDACO_MARKER_COLOR,
                'highlightColor': settings.SINDACO_MARKER_HIGHLIGHT,
            }

            if incarico['charge_type'] == "http://api3.openpolis.it/politici/chargetypes/16":
                # commissari
                # todo: add dummy image for commissario
                # todo: aggiungere motivo commissariamento
                dict_widget['label'] = "Commissariamento".upper()
                dict_widget['icon'] = ''
                dict_widget['sublabel'] = incarico['description']

            elif incarico['charge_type'] == "http://api3.openpolis.it/politici/chargetypes/14":
                # sindaci

                # todo: add dummy image if sindaco doesn't have a pic

                # sets sindaco name, surname
                dict_widget['label'] = "{0}.{1}".\
                    format(
                        incarico['politician']['first_name'][0].upper(),
                        incarico['politician']['last_name'].upper().encode('utf-8'),
                    )

                dict_widget['icon'] = incarico['politician']['image_uri']

                # as a sublabel sets the party acronym, if it's not available then the party name is used
                if incarico['party']['acronym']:
                    dict_widget['sublabel'] = incarico['party']['acronym'].upper()
                elif incarico['party']['name']:
                    # removes text between parenthesis from party name
                    dict_widget['sublabel'] = re.sub(r'\([^)]*\)', '', incarico['party']['name']).upper()
                else:
                    dict_widget['sublabel']=''


            else:
                # incarico type not accepted
                return None

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

    def incarichi_date_check(self, incarichi_set):

        """
        Incarichi check checks that incarichi for a given Comune are not overlapping and
        sets incarichi beginnings and end based on the start / end of web app timeline.

        Return a tuple (Bool, incarichi_set)
        """


        # converts all textual data to datetime obj type and
        # discards incarichi out of timeline scope: happened before timeline_start or after timeline_end

        incarichi_clean_set = []
        for incarico in incarichi_set:

            incarico['date_start'] = time.strptime(incarico['date_start'], self.date_fmt)
            if incarico['date_end']:
                incarico['date_end'] = time.strptime(incarico['date_end'], self.date_fmt)

            # considers only charges which are contained between self.timeline_start / end
            if ( incarico['date_end'] is None or incarico['date_end'] > self.timeline_start) and incarico['date_start'] < self.timeline_end:

                if incarico['date_end'] is None or incarico['date_end'] > self.timeline_end:
                    incarico['date_end'] = self.timeline_end

                if incarico['date_start']  < self.timeline_start:
                    incarico['date_start']  = self.timeline_start

                incarichi_clean_set.append(incarico)


        # checks if clean incarichi are overlapping
        for incarico_considered in incarichi_clean_set:
            considered_start = incarico_considered['date_start']
            considered_end = incarico_considered['date_end']

            for incarico_inner in incarichi_clean_set:
                if incarico_inner is not incarico_considered:
                    inner_start = incarico_inner['date_start']
                    inner_end = incarico_inner['date_end']

                    if inner_start < considered_start < inner_end:
                        return False, []
                    if inner_end > considered_end > inner_start:
                        return False, []


        return True, incarichi_clean_set


    def get_incarichi(self, territorio_opid):

        # get sindaci
        sindaci_api_results = self.get_incarichi_api(territorio_opid, incarico_type='14')

        # get commissari
        commissari_api_results = self.get_incarichi_api(territorio_opid, incarico_type='16')

        # unite data and check for data integrity
        api_results = sindaci_api_results
        api_results.extend(commissari_api_results)

        # if data is ok transform data format to fit Visup widget specs
        date_check, incarichi_set = self.incarichi_date_check(api_results)
        if date_check:

            return self.transform_incarichi(incarichi_set)

        else:
            # if data is not correct then turns off the sindaci timeline
            return incarichi_set


    ##
    # transform bilancio values to be feeded to Visup widget
    ##

    def transform_voce(self, voce_values, line_id, line_color):

        series_dict = {
            'id':line_id,
            'color':  line_color ,
            'series':[]
        }

        for voce_value in voce_values:
            series_dict['series'].append(
                [voce_value.anno, voce_value.valore]
            )

        return series_dict

    ##
    # get bilancio values of specified Voce for Territorio in the time span
    ##

    def get_voce(self, territorio, voce_bilancio, line_id, line_color):

        voce_values = ValoreBilancio.objects.filter(
            territorio = territorio,
            voce = voce_bilancio,
            anno__gte = self.timeline_start.tm_year,
            anno__lte = self.timeline_end.tm_year
        ).order_by('anno')

        return self.transform_voce(voce_values, line_id, line_color)


class IncarichiVoceJSONView(View, IncarichiGetterMixin):
    def get(self, request, **kwargs):

        # get territorio_opid from GET parameter
        territorio_opid = kwargs['territorio_opid']
        territorio = get_object_or_404(Territorio, op_id = territorio_opid)

        # gets the Territorio that is the cluster to which the considered territorio belongs
        cluster = Territorio.objects.get(
            territorio = Territorio.TERRITORIO.L,
            cluster = territorio.cluster,
        )

        # get voce bilancio from GET parameter
        voce_slug = kwargs['voce_slug']
        if voce_slug:
            voce_bilancio = get_object_or_404(Voce, slug = voce_slug)
        else:
            return



        incarichi_set = self.get_incarichi(territorio_opid)

        # gets voce value for the territorio over the period set
        voce_set = self.get_voce(territorio, voce_bilancio, line_id=1, line_color=settings.MAIN_LINE_COLOR)

        cluster_mean_set = self.get_voce(cluster, voce_bilancio, line_id=2, line_color=settings.CLUSTER_LINE_COLOR)

        legend = [
            {
              "color": settings.MAIN_LINE_COLOR,
              "id": 1,
              "label": voce_bilancio.denominazione.upper()
            },
            {
              "color": settings.CLUSTER_LINE_COLOR,
              "id": 2,
              "label": 'MEDIA CLUSTER "' + cluster.denominazione.upper()+'"'
            },

        ]


        return HttpResponse(
            content=json.dumps(
                {
                    "timeSpans":[incarichi_set],
                    'data':[cluster_mean_set, voce_set],
                    'legend':legend
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


class ConfrontiRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        # transforms the territorio_pk to territorio_slug to create a readable URL for Comuni confronti

        territorio_1 = get_object_or_404(Territorio, pk=int(self.request.GET.get('territorio_1',0)))
        territorio_2 = get_object_or_404(Territorio, pk=int(self.request.GET.get('territorio_2',0)))

        if territorio_1 == territorio_2:
            return reverse('home')

        kwargs['territorio_1_slug'] = territorio_1.slug
        kwargs['territorio_2_slug'] = territorio_2.slug

        try:
            url = reverse('confronti-data', args=args , kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url



class ConfrontiHomeView(TemplateView):

    ##
    # ConfrontiHomeView shows the search form to compare two Territori
    ##

    template_name = "bilanci/confronti.html"

    def get_context_data(self, **kwargs):

        # generates the list of bilancio Voce and Indicators
        # for the selection menu displayed on page

        context = {'territori_comparison_search_form': TerritoriComparisonSearchForm(),
                   'indicator_list': Indicatore.objects.all().order_by('denominazione'),
                   'voci_bilancio_list': Voce.objects.all().order_by('denominazione')}


        return context


class ConfrontiDataView(ConfrontiHomeView):

    ##
    # ConfrontiDataView shows the complete comparison of two Territori
    ##


    def get(self, request, *args, **kwargs):

        if 'territorio_1_slug' not in kwargs.keys() or 'territorio_2_slug' not in kwargs.keys():
            return redirect('home')

        else:
            territorio_1_slug = kwargs['territorio_1_slug']
            territorio_2_slug = kwargs['territorio_2_slug']

            # avoids showing a comparison with a Territorio with itself
            # redirects to home page
            if territorio_2_slug == territorio_1_slug:
                return redirect('home')

        return super(ConfrontiDataView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(ConfrontiDataView, self).get_context_data(**kwargs)

        territorio_1 = get_object_or_404(Territorio, slug = kwargs['territorio_1_slug'])
        territorio_2 = get_object_or_404(Territorio, slug = kwargs['territorio_2_slug'])

        context['territorio_1'] = territorio_1
        context['territorio_2'] = territorio_2
        context['territori_comparison_search_form'] = \
            TerritoriComparisonSearchForm(
                initial={'territorio_1': territorio_1, 'territorio_2': territorio_2}
            )


        return context