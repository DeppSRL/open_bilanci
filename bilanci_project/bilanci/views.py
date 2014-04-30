from itertools import groupby
from operator import itemgetter
import os
from pprint import pprint
import re
import json
import zmq
from collections import OrderedDict
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView, View, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
from bilanci.forms import TerritoriComparisonSearchForm, EarlyBirdForm
from bilanci.models import ValoreBilancio, Voce, Indicatore, ValoreIndicatore
from django.http.response import HttpResponse, HttpResponseRedirect, Http404
from bilanci.utils import couch

from territori.models import Territorio, Contesto, Incarico


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"


class HomeTemporaryView(TemplateView):
    template_name = "home_temporary.html"

    def get_context_data(self, **kwargs):
        context = super(HomeTemporaryView, self).get_context_data( **kwargs)
        context['form'] = EarlyBirdForm()
        return  context

    def post(self, request, *args, **kwargs):
        ##
        # Send form data to the mailbin queue
        ##

        context = self.get_context_data( **kwargs)

        context['form']  = form = EarlyBirdForm(self.request.POST)

        if form.is_valid():
            z_context = zmq.Context()
            # socket to sending messages to save
            save_sender = z_context.socket(zmq.PUSH)

            try:
                save_sender.connect(settings.MAILBIN_QUEUE_ADDR)
            except Exception, e:
                print "Error connecting: %s" % e

            data = {
                'first_name': request.POST['nome'],
                'last_name': request.POST['cognome'],
                'email': request.POST['email'],
                'ip_address': request.META['REMOTE_ADDR'],
                'user_agent': request.META['HTTP_USER_AGENT'],
                'service_uri': 'http://www.openbilanci.it/'
            }


            # send message to receiver
            save_sender.send_json(data)
            context['sent_data'] = True
        else:
            context['has_errors']=True
        return self.render_to_response(context)




class IndicatorSlugVerifierMixin(object):

    ##
    # IndicatorSlugVerifier given a slug list of Indicatore verifies that all slug exist
    # returns a list of those slugs that were verified
    ##

    def verify_slug(self,slug_list):

        verified_slug_list =[]
        # verify that all indicators exist and creates a verified list of slugs
        for ind_slug in slug_list:
            try:
                Indicatore.objects.get(slug = ind_slug)
            except ObjectDoesNotExist:
                pass
            else:
                verified_slug_list.append(ind_slug)

        return verified_slug_list

class IncarichiGetterMixin(object):
    
    date_fmt = '%Y-%m-%d'
    #     sets the start / end of graphs
    timeline_start = settings.TIMELINE_START_DATE
    timeline_end = settings.TIMELINE_END_DATE
    
    def transform_incarichi(self, incarichi_set, highlight_color):

        incarichi_transformed = []
        for incarico in incarichi_set:

            dict_widget = {
                'start':  incarico.data_inizio.strftime(self.date_fmt),
                'end': incarico.data_fine.strftime(self.date_fmt),

                # sets incarico marker color and highlight
                'icon': settings.INCARICO_MARKER_DUMMY,
                'color': settings.INCARICO_MARKER_INACTIVE,
                'highlightColor': highlight_color,
            }

            if incarico.pic_url:
                dict_widget['icon'] = incarico.pic_url

            if incarico.tipologia == Incarico.TIPOLOGIA.commissario:
                # commissari
                dict_widget['label'] = "Commissariamento".upper()
                dict_widget['sublabel'] = incarico.motivo_commissariamento.title()

            else:

                # sets sindaco / vicesindaco name, surname
                dict_widget['label'] = "{0}.{1}".\
                    format(
                        incarico.nome[0].upper(),
                        incarico.cognome.upper().encode('utf-8'),
                    )

                if incarico.tipologia == Incarico.TIPOLOGIA.vicesindaco_ff :
                    # vicesindaco ff
                    dict_widget['sublabel'] = "Vicesindaco f.f.".upper()

                else:
                    # sindaci

                    # as a sublabel sets the party acronym, if it's not available then the party name is used
                    if incarico.party_acronym:
                        dict_widget['sublabel'] = incarico.party_acronym.upper()
                    elif incarico.party_name:
                        # removes text between parenthesis from party name
                        dict_widget['sublabel'] = re.sub(r'\([^)]*\)', '', incarico.party_name).upper()
                    else:
                        dict_widget['sublabel']=''



            incarichi_transformed.append(dict_widget)

        return incarichi_transformed



    def get_incarichi_struct(self, territorio_opid, highlight_color):

        incarichi_set = Incarico.objects.filter(territorio=Territorio.objects.get(op_id=territorio_opid))
        return self.transform_incarichi(incarichi_set, highlight_color)


    ##
    # transform bilancio values to be feeded to Visup widget
    ##

    def transform_for_widget(self, voce_values, line_id, line_color, decimals=0, values_type='real', per_capita = False):

        line_dict = {
            'id':line_id,
            'color':  line_color ,
            'series':[]
        }

        serie = []

        for voce_value in voce_values:

            # considers absolute or per_capita values
            if per_capita is False:
                value_to_consider = voce_value.valore
            else:
                value_to_consider = voce_value.valore_procapite

            if value_to_consider is not None:
                # real values are multiplied by GDP_DEFLATOR rates
                if values_type == 'real':
                    valore = value_to_consider * settings.GDP_DEFLATORS[voce_value.anno]
                else:
                    valore = value_to_consider

                serie.append(
                    [voce_value.anno, round(valore,decimals)]
                )
            else:
                serie.append(
                    [voce_value.anno, None]
                )

        # before returning the data struct checks if there is any missing year in the data set:
        # if so adds a list of [missing_year, None] to the serie: this creates a gap in the line chart

        fill_in = False
        for idx, [year, valore] in enumerate(serie):
            if idx != 0:
                prev_yr = serie[idx-1][0]
                yr_difference = year - prev_yr
                if yr_difference > 1:
                    fill_in_yr = prev_yr + 1
                    while fill_in_yr <= year -1 :
                        serie.append([fill_in_yr,None])
                        fill_in = True
                        fill_in_yr +=1


        # after inserting the fill-in years re-orders the list based on the year value: if this is not performed
        # the gap is not displayed on the graph
        if fill_in:
            line_dict['series'] = sorted(serie, key=lambda data: data[0])
        else:
            line_dict['series'] = serie

        return line_dict

    ##
    # get bilancio values of specified Voce for Territorio in the time span
    ##

    def get_voce_struct(self, territorio, voce_bilancio, line_id, line_color, values_type='real', per_capita = False):

        voce_values = ValoreBilancio.objects.filter(
            territorio = territorio,
            voce = voce_bilancio,
            anno__gte = self.timeline_start.year,
            anno__lte = self.timeline_end.year
        ).order_by('anno')

        return self.transform_for_widget(voce_values, line_id, line_color, values_type=values_type, per_capita=per_capita)

    ##
    # get indicatori values of specified Indicatore for Territorio in the time span
    ##

    def get_indicatore_struct(self, territorio, indicatore, line_id, line_color):

        indicatore_values = ValoreIndicatore.objects.filter(
            territorio = territorio,
            indicatore = indicatore,
            anno__gte = self.timeline_start.year,
            anno__lte = self.timeline_end.year
        ).order_by('anno')

        return self.transform_for_widget(indicatore_values, line_id, line_color, decimals=2)


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


        incarichi_set = self.get_incarichi_struct(territorio_opid, highlight_color = settings.TERRITORIO_1_COLOR)

        # gets voce value for the territorio over the period set
        # check nominal or real values in query string
        voce_set = self.get_voce_struct(
            territorio,
            voce_bilancio,
            line_id=1,
            line_color=settings.TERRITORIO_1_COLOR,
            values_type=self.request.GET.get('values_type', 'real'),
            per_capita= True
        )

        cluster_mean_set = self.get_voce_struct(
            cluster,
            voce_bilancio,
            line_id=2,
            line_color=settings.CLUSTER_LINE_COLOR,
            values_type=self.request.GET.get('values_type', 'real'),
            per_capita=True
        )

        legend = [
            {
              "color": settings.TERRITORIO_1_COLOR,
              "id": 1,
              "label": voce_bilancio.denominazione.upper()
            },
            {
              "color": settings.CLUSTER_LINE_COLOR,
              "id": 2,
              "label": 'MEDIANA CLUSTER "' + cluster.denominazione.upper()+'"'
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


class IncarichiIndicatoriJSONView(View, IncarichiGetterMixin, IndicatorSlugVerifierMixin):
    def get(self, request, **kwargs):

        # get territorio_opid from GET parameter
        territorio_opid = kwargs['territorio_opid']
        territorio = get_object_or_404(Territorio, op_id = territorio_opid)

        # get indicatori slug from GET parameter
        indicatori_slug_list = self.verify_slug(request.GET.getlist('slug'))
        indicatori = Indicatore.objects.filter(slug__in = indicatori_slug_list)

        if len(indicatori) == 0:
            return HttpResponse()

        incarichi_set = self.get_incarichi_struct(territorio_opid, highlight_color = settings.TERRITORIO_1_COLOR)

        # gets voce value for the territorio over the period set
        indicatori_set = []
        legend_set = []
        for indicator_num, indicatore in enumerate(indicatori):
            indicatori_set.append(self.get_indicatore_struct(territorio, indicatore, line_id=indicator_num, line_color=settings.INDICATOR_COLORS[indicator_num]))
            legend_set.append(
                {
                "color": settings.INDICATOR_COLORS[indicator_num],
                "id": indicator_num,
                "label": indicatore.denominazione.upper()
                }
            )

        return HttpResponse(
            content=json.dumps(
                {
                    "timeSpans":[incarichi_set],
                    'data':indicatori_set,
                    'legend':legend_set
                }
            ),
            content_type="application/json"
        )


class BilancioCompositionWidgetView(LoginRequiredMixin, TemplateView):

    template_name = None
    serie_start_year = settings.TIMELINE_START_DATE.year
    serie_end_year = settings.TIMELINE_END_DATE.year
    territorio = None

    def get(self, request, *args, **kwargs):
        self.values_type = self.request.GET.get('values_type', 'real')
        self.cas_com_type = self.request.GET.get('cas_com_type', 'cassa')
        return super(BilancioCompositionWidgetView, self).get(self, request, *args, **kwargs)


    def create_composition_data(self, main_bilancio_year, main_bilancio_slug, comparison_bilancio_year, comparison_bilancio_slug):

        composition_data = []

        ##
        # Create composition data retrieves the data needed to feed the composition widget:
        # * gets the complete set of values during the years
        #   for main_bilancio_slug which is the root node of preventivo/consuntivo entrate/spese
        # * gets the value for the comparison bilancio for a specific year
        # * loops over the results to create the data struct to be returned
        ##
        totale_label = 'Totale'
        comparison_not_available = False
        main_rootnode = Voce.objects.get(slug=main_bilancio_slug)
        main_nodes = main_rootnode.get_descendants(include_self=True).filter(level__lte=main_rootnode.level+1)

        comparison_rootnode = Voce.objects.get(slug=comparison_bilancio_slug)
        comparison_nodes = comparison_rootnode.get_descendants(include_self=True).filter(level__lte=comparison_rootnode.level+1)

        main_values = ValoreBilancio.objects.filter(
            voce__in= main_nodes,
            anno__gte=self.serie_start_year,
            anno__lte=self.serie_end_year,
            territorio=self.territorio
            ).values('voce__denominazione','voce__level','anno','valore','valore_procapite').order_by('voce__denominazione','anno')

        comparison_values = ValoreBilancio.objects.filter(
            voce__in=comparison_nodes,
            anno = comparison_bilancio_year,
            territorio=self.territorio
        ).values('voce__denominazione', 'voce__level', 'anno','valore','valore_procapite').order_by('voce__denominazione','anno')

        if len(comparison_values) == 0:
            comparison_not_available = True

        # regroup the main and comparison value set based on voce__denominazione
        # to match the rootnode the label Totale is used when needed

        main_keygen = lambda x: totale_label if x['voce__level'] == main_rootnode.level else x['voce__denominazione'].strip()
        main_values_regroup = dict((k,list(v)) for k,v in groupby(main_values, key=main_keygen))

        comparison_keygen = lambda x: totale_label if x['voce__level'] == comparison_rootnode.level else x['voce__denominazione'].strip()
        comparison_values_regroup = dict((k,list(v)[0]) for k,v in groupby(comparison_values, key=comparison_keygen))

        # assign correct GDP deflators (1 is assigned to nominal values)
        if self.values_type == 'real':
            main_gdp_deflator = settings.GDP_DEFLATORS[int(main_bilancio_year)]
            comparison_gdp_deflator = settings.GDP_DEFLATORS[int(comparison_bilancio_year)]
        else:
            main_gdp_deflator = 1.0
            comparison_gdp_deflator = 1.0

        # insert all the children values in the data struct
        for main_value_denominazione, main_value_set in main_values_regroup.iteritems():

            # creates value dict
            value_dict = dict(label = main_value_denominazione, series = [], total = False)

            # if the value considered is a total value then sets the appropriate flag
            if main_value_denominazione == totale_label:
                value_dict['total'] = True

            # unpacks year values for the considered voice of entrate/spese
            for index, single_value in enumerate(main_value_set):

                value_dict['series'].append([single_value['anno'], single_value['valore']])


                if single_value['anno'] == main_bilancio_year:
                    value_dict['value'] = single_value['valore'] * main_gdp_deflator
                    value_dict['procapite'] = single_value['valore_procapite'] * main_gdp_deflator


                    #calculate the % of variation between main_bilancio and comparison bilancio

                    variation = 0
                    if comparison_not_available is False:
                        comparison_value = float(comparison_values_regroup[main_value_denominazione]['valore']) * comparison_gdp_deflator
                        if comparison_value != 0:
                            single_value = float(single_value['valore']) * main_gdp_deflator
                            variation = ((single_value-comparison_value)/ comparison_value)*100.0
                        else:
                            # todo: what to do when a value passes from 0 to N?
                            variation = 999.0

                    # sets 2 digit precision for variation after decimal point

                    value_dict['variation'] = round(variation,2)


            composition_data.append(value_dict)

        return composition_data


    def get_context_data(self, widget_type, territorio_slug, bilancio_year, bilancio_type, **kwargs):

        context = super(BilancioCompositionWidgetView, self).get_context_data( **kwargs)

        ##
        # sets the correct template_name based on the type of rappresentation needed
        # gets the specified bilancio based on kwargs
        # identifies the bilancio to compare it with
        # creates the context to feed the Visup composition widget
        ##

        # composition data is the data struct to be passed to the context
        composition_data = {'hover': True, 'showLabels':False}

        if self.cas_com_type == 'competenza':
            entrate_consuntivo_slug = 'consuntivo-entrate-accertamenti'
            spese_consuntivo_slug = 'consuntivo-spese-impegni-spese-correnti-funzioni'
        else:
            entrate_consuntivo_slug = 'consuntivo-entrate-cassa'
            spese_consuntivo_slug = 'consuntivo-spese-cassa-spese-correnti-funzioni'


        entrate_slug = {
            'preventivo': 'preventivo-entrate',
            'consuntivo': entrate_consuntivo_slug,
        }

        spese_slug = {
            'preventivo': 'preventivo-spese-spese-correnti-funzioni',
            'consuntivo': spese_consuntivo_slug,
        }


        if widget_type == 'overview':
            self.template_name = 'bilanci/composizione_bilancio.html'

        #     debug: only for visup testing
        elif widget_type =='overview_new':
            self.template_name = 'bilanci/composizione_bilancio_new.html'
        #  / debug
        else:
            self.template_name = 'bilanci/composizione_entrate_uscite.html'

        territorio_slug = territorio_slug
        self.territorio = get_object_or_404(Territorio, slug = territorio_slug)

        main_bilancio_year = int(bilancio_year)
        main_bilancio_type = bilancio_type

        composition_data['year'] = main_bilancio_year

        # identifies the bilancio for comparison

        comparison_bilancio_type = None
        if main_bilancio_type == 'preventivo':
            comparison_bilancio_type = 'consuntivo'
            comparison_bilancio_year = main_bilancio_year-1
        else:
            comparison_bilancio_type = 'preventivo'
            comparison_bilancio_year = main_bilancio_year


        composition_data['entrate'] = self.create_composition_data(main_bilancio_year, entrate_slug[main_bilancio_type],comparison_bilancio_year, entrate_slug[comparison_bilancio_type])
        composition_data['spese'] = self.create_composition_data(main_bilancio_year,spese_slug[main_bilancio_type] , comparison_bilancio_year, spese_slug[comparison_bilancio_type])

        composition_data['widget1']=\
            {
            "label": "Indicatore",
            "series": [
                [2008,0.07306034071370959],
                [2009, 0.1824505201075226 ],
                [2010,0.9171787116210908],
                [2011,None],
                [2012,0.4342076904140413]
            ],
            "variation": -10,
            "sublabel1": "Propensione all'investimento",
            "sublabel2": "Rispetto a preventivo 2010",
            "sublabel3": "Andamento 2008-2012"
          }
        composition_data['widget2']=composition_data['widget1']
        composition_data['widget3']=composition_data['widget1']

        context['composition_data']=json.dumps(composition_data)

        return context


class ConfrontiDataJSONView(View, IncarichiGetterMixin):
    ##
    # Constuct a JSON structur to feed the Visup widget
    #
    # The struct contains
    # * Incarichi for Territorio 1 , 2
    # * Data set for Indicator / Voce Bilancio selected
    # * Legend data
    ##


    
    def get(self, request, **kwargs):

        # get territorio_opid from GET parameter
        territorio_1_color = settings.TERRITORIO_1_COLOR
        territorio_2_color = settings.TERRITORIO_2_COLOR

        territorio_1_opid = kwargs['territorio_1_opid']
        territorio_2_opid = kwargs['territorio_2_opid']

        territorio_1 = get_object_or_404(Territorio, op_id = territorio_1_opid)
        territorio_2 = get_object_or_404(Territorio, op_id = territorio_2_opid)

        incarichi_set_1 = self.get_incarichi_struct(territorio_1_opid, highlight_color = territorio_1_color)
        incarichi_set_2 = self.get_incarichi_struct(territorio_2_opid, highlight_color = territorio_2_color)

        # get voce bilancio from GET parameter
        parameter_slug = kwargs['parameter_slug']
        parameter_type = kwargs['parameter_type']

        if parameter_slug:
            if parameter_type == 'indicatori':
                indicatore = get_object_or_404(Indicatore, slug = parameter_slug)
                # gets indicator value for the territorio over the period set
                data_set_1 = self.get_indicatore_struct(territorio_1, indicatore, line_id=1, line_color = territorio_1_color)
                data_set_2 = self.get_indicatore_struct(territorio_2, indicatore, line_id=2, line_color = territorio_2_color)

            elif parameter_type == 'entrate' or parameter_type == 'spese':
                voce_bilancio = get_object_or_404(Voce, slug = parameter_slug)
                # gets voce value for the territorio over the period set
                data_set_1 = self.get_voce_struct(territorio_1, voce_bilancio, line_id=1, line_color = territorio_1_color, per_capita=True)
                data_set_2 = self.get_voce_struct(territorio_2, voce_bilancio, line_id=2, line_color = territorio_2_color, per_capita=True)

            else:
                return reverse('404')

        else:
            return reverse('404')


        legend = [
            {
              "color": territorio_1_color,
              "id": 1,
              "label": "{0}".format(territorio_1.denominazione)
            },
            {
              "color": territorio_2_color,
              "id": 2,
              "label": "{0}".format(territorio_2.denominazione)
            },
        ]

        data = [data_set_1, data_set_2]

        return HttpResponse(
            content=json.dumps(
                {
                    "timeSpans":[incarichi_set_1, incarichi_set_2],
                    'data':data,
                    'legend':legend
                }
            ),
            content_type="application/json"
        )
    


class BilancioRedirectView(LoginRequiredMixin, RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        territorio = get_object_or_404(Territorio, slug=self.request.GET.get('territori',0))

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
                url = reverse('bilanci-overview', args=args , kwargs=kwargs)
            except NoReverseMatch:
                return reverse('404')

            return url + '?year=' + year +"&type=" + tipo_bilancio
        else:
            return reverse('404')


class BilancioView(LoginRequiredMixin, DetailView):

    model = Territorio
    context_object_name = "territorio"
    territorio= None

    def get_complete_file(self, file_name):
        """
        Return a dict with file_name and file_size, if a file exists,
        None if the file does not exist.
        """

        file_path = os.path.join(settings.OPENDATA_ROOT, file_name)
        if os.path.isfile(file_path):
            file_size = os.stat(file_path).st_size
            return {
                'file_name': file_name,
                'file_size': file_size
            }
        else:
            return {}

    def get_context_data(self, **kwargs ):
        context = super(BilancioView, self).get_context_data(**kwargs)

        territorio = self.get_object()
        csv_package_filename = "{0}.zip".format(territorio.cod_finloc)
        context['csv_package_file'] = self.get_complete_file(csv_package_filename)
        context['open_data_url'] = settings.OPENDATA_URL
        return context


class BilancioOverView(BilancioView):
    template_name = 'bilanci/bilancio_overview.html'
    selected_section = "bilancio"

    def get(self, request, *args, **kwargs):

        ##
        # if year or type parameter are missing redirects to a page for default year / default bilancio type
        ##

        must_redirect = False
        self.territorio = self.get_object()

        self.year = self.request.GET.get('year', settings.SELECTOR_DEFAULT_YEAR)
        try:
            best_bilancio = self.territorio.best_bilancio_type(self.year)
        except Exception:
            return HttpResponseRedirect(reverse('404'))

        if 'type' in self.request.GET and self.request.GET['type'] == 'consuntivo' and \
            best_bilancio == 'preventivo':
            must_redirect = True

        if self.selected_section == 'bilancio':
            self.tipo_bilancio = best_bilancio
            if 'type' in self.request.GET and self.request.GET['type'] != self.tipo_bilancio:
                must_redirect = True
        else:
            if not must_redirect:
                self.tipo_bilancio = self.request.GET.get('type', best_bilancio)
            else:
                self.tipo_bilancio = self.request.GET.get('type', best_bilancio)

        self.values_type = self.request.GET.get('values_type', 'real')
        self.cas_com_type = self.request.GET.get('cas_com_type', 'cassa')
        self.fun_int_view = self.request.GET.get('fun_int_view', 'funzioni')

        qs = self.request.META['QUERY_STRING']
        must_redirect = (len(qs.split('&')) < 4) or must_redirect


        if must_redirect:
            destination_view = 'bilanci-overview'

            if self.selected_section == 'entrate':
                destination_view = 'bilanci-entrate'
            elif self.selected_section == 'spese':
                destination_view = 'bilanci-spese'

            return HttpResponseRedirect(
                reverse(destination_view, kwargs={'slug':self.territorio.slug}) +\
                "?year={0}&type={1}&values_type={2}&cas_com_type={3}".format(
                    self.year, self.tipo_bilancio,
                    self.values_type, self.cas_com_type))

        return super(BilancioOverView, self).get(self, request, *args, **kwargs)


    def get_context_data(self, **kwargs ):

        context = super(BilancioOverView, self).get_context_data(**kwargs)
        
        query_string = self.request.META['QUERY_STRING']

        context['tipo_bilancio'] = self.tipo_bilancio
        context['selected_bilancio_type'] = self.tipo_bilancio

        menu_voices_kwargs = {'slug': self.territorio.slug}

        context['selected_section']=self.selected_section
        # get Comune context data from db
        context['comune_context'] = Contesto.get_context(self.year, self.territorio)
        context['territorio_opid'] = self.territorio.op_id
        context['query_string'] = query_string
        context['selected_year'] = self.year
        context['selector_default_year'] = settings.SELECTOR_DEFAULT_YEAR
        context['values_type'] = self.values_type
        context['cas_com_type'] = self.cas_com_type


        context['menu_voices'] = OrderedDict([
            ('bilancio', reverse('bilanci-overview', kwargs=menu_voices_kwargs)),
            ('entrate', reverse('bilanci-entrate', kwargs=menu_voices_kwargs)),
            ('spese', reverse('bilanci-spese', kwargs=menu_voices_kwargs)),
            ('indicatori', reverse('bilanci-indicatori', kwargs=menu_voices_kwargs))
        ])

        return context

class BilancioIndicatoriView(LoginRequiredMixin, DetailView, IndicatorSlugVerifierMixin):
    model = Territorio
    context_object_name = "territorio"
    template_name = 'bilanci/bilancio_indicatori.html'
    selected_section = "indicatori"
    territorio = None
    
    def get(self, request, *args, **kwargs):

        ##
        # if parameter is missing redirects to a page for default indicator
        ##
        self.territorio = self.get_object()

        if self.request.GET.get('slug') is None:
            return HttpResponseRedirect(reverse('bilanci-indicatori', kwargs={'slug':self.territorio.slug})\
                                        + "?slug={0}".format(settings.DEFAULT_INDICATOR_SLUG))

        return super(BilancioIndicatoriView, self).get(self, request, *args, **kwargs)



    def get_context_data(self, **kwargs ):

        context = super(BilancioIndicatoriView, self).get_context_data(**kwargs)
        
        menu_voices_kwargs = {'slug':self.territorio.slug}

        # get selected indicatori slug list from request and verifies them
        selected_indicators_slugs = self.verify_slug(self.request.GET.getlist('slug'))

        context['selected_section']=self.selected_section
        # get Comune context data from db
        year = settings.SELECTOR_DEFAULT_YEAR

        context['comune_context'] = Contesto.get_context(year,self.territorio)
        context['territorio_opid'] =self.territorio.op_id

        context['menu_voices'] = OrderedDict([
            ('bilancio', reverse('bilanci-overview', kwargs=menu_voices_kwargs)),
            ('entrate', reverse('bilanci-entrate', kwargs=menu_voices_kwargs)),
            ('spese', reverse('bilanci-spese', kwargs=menu_voices_kwargs)),
            ('indicatori', reverse('bilanci-indicatori', kwargs=menu_voices_kwargs))
        ])

        context['indicator_list'] = Indicatore.objects.all().order_by('denominazione')

        # creates the query string to call the IncarichiIndicatori Json view in template
        context['selected_indicators'] = selected_indicators_slugs
        context['selected_indicators_qstring'] = '?slug='+'&slug='.join(selected_indicators_slugs)
        return context


class BilancioDetailView(BilancioOverView):

    def get_slug(self):
        raise Exception("Not implemented in base class.")

    def get_context_data(self, **kwargs ):

        context = super(BilancioDetailView, self).get_context_data(**kwargs)
        territorio = self.get_object()
        query_string = self.request.META['QUERY_STRING']

        voce_slug = self.get_slug()

        # gets the tree structure from db
        bilancio_rootnode = Voce.objects.get(slug = voce_slug)

        # gets the part of bilancio data which is referring to Voce nodes which are
        # descendants of bilancio_treenodes to minimize queries and data size
        budget_values = ValoreBilancio.objects.filter(territorio = territorio, anno=self.year).\
            filter(voce__in=bilancio_rootnode.get_descendants(include_self=True).values_list('pk', flat=True))

        values_type = self.values_type

        absolute_values = budget_values.values_list('voce__slug', 'valore')
        percapita_values = budget_values.values_list('voce__slug', 'valore_procapite')
        if values_type == 'real':
            absolute_values = dict(
                map(
                    lambda x: (x[0], x[1] * settings.GDP_DEFLATORS[int(self.year)]),
                    absolute_values
                )
            )
            percapita_values = dict(
                map(
                    lambda x: (x[0], x[1] * settings.GDP_DEFLATORS[int(self.year)]),
                    percapita_values
                )
            )

        context['budget_values'] = {
            'absolute': dict(absolute_values),
            'percapita': dict(percapita_values)
        }


        # checks if political context data is available to show/hide timeline widget in the template
        context['show_timeline'] = True
        incarichi_set = Incarico.objects.filter(territorio=Territorio.objects.get(op_id=territorio.op_id))
        if len(incarichi_set) == 0:
            context['show_timeline'] = False

        context['bilancio_rootnode'] = bilancio_rootnode
        context['bilancio_tree'] =  bilancio_rootnode.get_descendants(include_self=True)

        context['query_string'] = query_string

        context['year'] = self.year

        return context


class BilancioEntrateView(BilancioDetailView):
    template_name = 'bilanci/bilancio_entrate.html'
    selected_section = "entrate"

    def get_slug(self):
        cassa_competenza_type = self.cas_com_type
        if self.cas_com_type == 'competenza':
            cassa_competenza_type = 'accertamenti'

        if self.tipo_bilancio == 'preventivo':
            return "{0}-{1}".format(self.tipo_bilancio,"entrate")
        else:
            return "{0}-{1}".format(
                self.tipo_bilancio,
                "entrate-{0}".format(cassa_competenza_type)
            )



class BilancioSpeseView(BilancioDetailView):
    template_name = 'bilanci/bilancio_spese.html'
    selected_section = "spese"

    def get_slug(self):
        cassa_competenza_type = self.cas_com_type
        if self.cas_com_type == 'competenza':
            cassa_competenza_type = 'impegni'

        if self.tipo_bilancio == 'preventivo':
            return "{0}-{1}".format(self.tipo_bilancio,"spese")
        else:
            return "{0}-{1}".format(
                self.tipo_bilancio,
                "spese-{0}".format(cassa_competenza_type)
            )


    def get_context_data(self, **kwargs):
        """
        Extend the context with funzioni/interventi view and switch variables
        """

        context = super(BilancioSpeseView, self).get_context_data(**kwargs)

        full_path = self.request.get_full_path()
        if not 'fun_int_view' in full_path:
            fun_int_switch_url = full_path + "&fun_int_view=interventi"
        else:
            if self.fun_int_view == 'funzioni':
                fun_int_switch_url = full_path.replace("&fun_int_view=funzioni", "&fun_int_view=interventi")
            else:
                fun_int_switch_url = full_path.replace("&fun_int_view=interventi", "&fun_int_view=funzioni")


        context['fun_int_current_view'] = self.fun_int_view
        context['fun_int_switch'] = {
            'label': 'interventi' if self.fun_int_view == 'funzioni' else 'funzioni',
            'url': fun_int_switch_url
        }

        return context


class ClassificheRedirectView(LoginRequiredMixin, RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        # redirects to appropriate confronti view based on default parameter for Territori
        # todo: define in settings default parameter for Classifiche
        kwargs['parameter_type'] = 'indicatori'
        kwargs['parameter_slug'] = Indicatore.objects.all()[0].slug
        kwargs['anno'] = settings.SELECTOR_DEFAULT_YEAR

        try:
            url = reverse('classifiche-list', args=args , kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url

class ClassificheListView(LoginRequiredMixin, ListView):

    template_name = 'bilanci/classifiche.html'
    paginate_by = 20
    parameter_type = None
    parameter = None
    anno = None

    def get(self, request, *args, **kwargs):

        # checks that parameter type is correct
        # checks that parameter slug exists

        self.parameter_type = kwargs['parameter_type']
        self.anno = kwargs['anno']
        parameter_slug = kwargs['parameter_slug']

        if self.parameter_type == 'indicatori':
            self.parameter = get_object_or_404(Indicatore, slug = parameter_slug)
        elif self.parameter_type == 'entrate' or self.parameter_type == 'spese':
            self.parameter = get_object_or_404(Voce, slug = parameter_slug)
        else:
            return reverse('404')

        return super(ClassificheListView, self).get(self, request, *args, **kwargs)

    def get_queryset(self):

        if self.parameter_type == 'indicatori':
            return ValoreIndicatore.objects.filter(indicatore = self.parameter, territorio__territorio = 'C', anno = self.anno).order_by('-valore')
        else:
            return ValoreBilancio.objects.filter(voce = self.parameter, territorio__territorio = 'C', anno = self.anno).order_by('-valore')

    def get_context_data(self, **kwargs):

        context = super(ClassificheListView, self).get_context_data( **kwargs)

        # enrich the Queryset in object_list with Political context data
        valori_list = []
        for valoreObj in self.object_list:
            valori_list.append(
                {
                'territorio': valoreObj.territorio,
                'valore': valoreObj.valore,
                'incarichi_attivi': Incarico.get_incarichi_attivi(valoreObj.territorio, self.anno),
                }
            )

        context['valori_list'] = valori_list
        # defines the lists of possible confrontation parameters
        context['selected_par_type'] = self.parameter_type
        context['selected_parameter'] = self.parameter
        context['selected_year'] = self.anno
        context['selector_default_year'] = settings.SELECTOR_DEFAULT_YEAR
        context['indicator_list'] = Indicatore.objects.all().order_by('denominazione')
        context['entrate_list'] = Voce.objects.get(slug='consuntivo-entrate-cassa').get_children().order_by('slug')
        context['spese_list'] = Voce.objects.get(slug='consuntivo-spese-cassa-spese-correnti-funzioni').get_children().order_by('slug')

        context['regioni_list'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).order_by('denominazione')
        context['cluster_list'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.L).order_by('-cluster')

        return context


class ConfrontiHomeView(LoginRequiredMixin, TemplateView):

    ##
    # ConfrontiHomeView shows the search form to compare two Territori
    ##

    template_name = "bilanci/confronti_home.html"

    def get_context_data(self, **kwargs):

        # generates the list of bilancio Voce and Indicators
        # for the selection menu displayed on page

        context = {'territori_comparison_search_form': TerritoriComparisonSearchForm(),}


        return context


class ConfrontiRedirectView(LoginRequiredMixin, RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        # redirects to appropriate confronti view based on default parameter for Territori
        # todo: define in settings default indicator
        kwargs['parameter_slug'] = Indicatore.objects.all()[0].slug

        try:
            url = reverse('confronti-indicatori', args=args , kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url


class ConfrontiView(LoginRequiredMixin, TemplateView):

    template_name = "bilanci/confronti_data.html"

    territorio_1 = None
    territorio_2 = None


    def get(self, request, *args, **kwargs):


        territorio_1_slug = kwargs['territorio_1_slug']
        territorio_2_slug = kwargs['territorio_2_slug']

        # avoids showing a comparison with a Territorio with itself
        # redirects to home page
        if territorio_2_slug == territorio_1_slug:
            return redirect('confronti-home')

        self.territorio_1 = get_object_or_404(Territorio, slug = territorio_1_slug)
        self.territorio_2 = get_object_or_404(Territorio, slug = territorio_2_slug)

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)



    def get_context_data(self, **kwargs):

        # construct common context data for Confronti View
        context = super(ConfrontiView, self).get_context_data( **kwargs)

        context['territorio_1'] = self.territorio_1
        context['territorio_2'] = self.territorio_2

        context['contesto_1'] = self.territorio_1.latest_contesto
        context['contesto_2'] = self.territorio_2.latest_contesto


        # defines the lists of possible confrontation parameters
        context['indicator_list'] = Indicatore.objects.all().order_by('denominazione')
        context['entrate_list'] = Voce.objects.get(slug='consuntivo-entrate-cassa').get_children().order_by('slug')
        context['spese_list'] = Voce.objects.get(slug='consuntivo-spese-cassa-spese-correnti-funzioni').get_children().order_by('slug')

        context['territori_comparison_search_form'] = \
            TerritoriComparisonSearchForm(
                initial={
                    'territorio_1': self.territorio_1,
                    'territorio_2': self.territorio_2
                }
            )

        return context



class ConfrontiEntrateView(ConfrontiView):

    def get_context_data(self, **kwargs):
        context = super(ConfrontiEntrateView, self).get_context_data( **kwargs)
        context['parameter_type'] = "entrate"
        context['parameter'] = get_object_or_404(Voce, slug = kwargs['parameter_slug'])
        return context

class ConfrontiSpeseView(ConfrontiView):

    def get_context_data(self, **kwargs):
        context = super(ConfrontiSpeseView, self).get_context_data( **kwargs)
        context['parameter_type'] = "spese"
        context['parameter'] = get_object_or_404(Voce, slug = kwargs['parameter_slug'])


        return context

class ConfrontiIndicatoriView(ConfrontiView):

    def get_context_data(self, **kwargs):
        context = super(ConfrontiIndicatoriView, self).get_context_data( **kwargs)
        context['parameter_type'] = "indicatori"
        context['parameter'] = get_object_or_404(Indicatore, slug = kwargs['parameter_slug'])


        return context


