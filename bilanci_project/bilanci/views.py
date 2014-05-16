from itertools import groupby, ifilter
from operator import itemgetter
import os
import re
import json
import zmq
import requests
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
from shorturls.models import ShortUrl
from django.http.response import HttpResponse, HttpResponseRedirect, Http404
from bilanci.utils import couch

from territori.models import Territorio, Contesto, Incarico


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

class HomeReleaseView(LoginRequiredMixin, TemplateView):
    template_name = "home_release.html"

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

        voce_line_label = voce_bilancio.denominazione

        # if the voce is a voce used for the main linegraph the label is translated for better comprehension

        voce_slug_to_translate = {
            'preventivo-entrate': 'Totale entrate previste',
            'preventivo-spese': 'Totale spese previste',
            'consuntivo-entrate-cassa': 'Totale entrate incassate',
            'consuntivo-entrate-accertamenti': 'Totale entrate accertate',
            'consuntivo-spese-impegni': 'Totale entrate impegnate',
            'consuntivo-spese-cassa': 'Totale spese pagate'

        }

        if voce_bilancio.slug in voce_slug_to_translate.keys():

            voce_line_label = voce_slug_to_translate[voce_bilancio.slug]


        legend = [
            {
              "color": settings.TERRITORIO_1_COLOR,
              "id": 1,
              "label": voce_line_label.upper()
            },
            {
              "color": settings.CLUSTER_LINE_COLOR,
              "id": 2,
              "label": 'MEDIANA DEI COMUNI ' + cluster.denominazione.upper()+''
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
    show_help = True
    totale_label = "Totale"
    territorio = None
    serie_start_year = settings.TIMELINE_START_DATE.year
    serie_end_year = settings.TIMELINE_END_DATE.year
    widget_type = None
    main_gdp_deflator = comp_gdb_deflator = None
    main_gdp_multiplier = comp_gdp_multiplier = 1.0
    main_bilancio_year = main_bilancio_type = None
    comp_bilancio_year = comp_bilancio_type = None
    values_type = None
    cas_com_type = None


    def get(self, request, *args, **kwargs):
        self.values_type = self.request.GET.get('values_type', 'real')
        self.cas_com_type = self.request.GET.get('cas_com_type', 'cassa')
        self.main_bilancio_year = int(kwargs.get('bilancio_year', settings.APP_END_DATE.year ))
        self.main_bilancio_type = kwargs.get('bilancio_type','consuntivo')
        territorio_slug = kwargs.get('territorio_slug', None)
        self.widget_type = kwargs.get('widget_type', 'overview')

        if not territorio_slug:
            return reverse('404')

        self.territorio = get_object_or_404(Territorio, slug = territorio_slug)

        if self.widget_type == 'overview':
            self.template_name = 'bilanci/composizione_bilancio.html'

        else:
            self.template_name = 'bilanci/composizione_entrate_uscite.html'

        return super(BilancioCompositionWidgetView, self).get(self, request, *args, **kwargs)

    # calculates the % variation of main_value compared to comparison_values
    # adjusting the values with gdp deflator if needed

    def calculate_variation(self, main_val, comp_val, ):

        deflated_main_val = main_val
        deflated_comp_val = comp_val

        deflated_main_val = float(main_val) * self.main_gdp_multiplier
        deflated_comp_val = float(comp_val) * self.comp_gdp_multiplier

        if deflated_comp_val != 0:
            # sets 2 digit precision for variation after decimal point
            return round(((deflated_main_val-deflated_comp_val)/ deflated_comp_val)*100.0,2)
        else:
            # value passes from 0 to N:
            # variation would be infinite so variation is set to null
            return None


    def get_data_set(self, main_bilancio_slug, comp_bilancio_slug,):
        comp_not_available = False
        main_rootnode = Voce.objects.get(slug=main_bilancio_slug)
        main_nodes = main_rootnode.get_descendants(include_self=True).filter(level__lte=main_rootnode.level+1)

        comp_rootnode = Voce.objects.get(slug=comp_bilancio_slug)
        comparison_nodes = comp_rootnode.get_descendants(include_self=True).filter(level__lte=comp_rootnode.level+1)

        main_values = ValoreBilancio.objects.filter(
            voce__in= main_nodes,
            anno__gte=self.serie_start_year,
            anno__lte=self.serie_end_year,
            territorio=self.territorio
            ).values('voce__denominazione','voce__level','anno','valore','valore_procapite','voce__slug').order_by('voce__denominazione','anno')

        comp_values = ValoreBilancio.objects.filter(
            voce__in=comparison_nodes,
            anno = self.comp_bilancio_year,
            territorio=self.territorio
        ).values('voce__denominazione', 'voce__level', 'anno','valore','valore_procapite','voce__slug').order_by('voce__denominazione','anno')

        if len(comp_values) == 0:
            comp_not_available = True

        # regroup the main and comparison value set based on voce__denominazione
        # to match the rootnode the label Totale is used when needed

        main_keygen = lambda x: self.totale_label if x['voce__level'] == main_rootnode.level else x['voce__denominazione'].strip()
        main_values_regroup = dict((k,list(v)) for k,v in groupby(main_values, key=main_keygen))

        comp_keygen = lambda x: self.totale_label if x['voce__level'] == comp_rootnode.level else x['voce__denominazione'].strip()
        comp_values_regroup = dict((k,list(v)[0]) for k,v in groupby(comp_values, key=comp_keygen))


        widget_data = self.compose_widget_data(main_values_regroup, comp_values_regroup, comp_not_available )

        return main_values_regroup, comp_values_regroup, widget_data



    def compose_widget_data(self, main_values_regroup, comp_values_regroup, comp_not_available):
        composition_data = []

        ##
        # compose_widget_data
        # loops over the results to create the data struct to be returned
        ##

        for main_value_denominazione, main_value_set in main_values_regroup.iteritems():

            # creates value dict
            value_dict = dict(label = main_value_denominazione, series = [], total = False)

            # if the value considered is a total value then sets the appropriate flag
            if main_value_denominazione == self.totale_label:
                value_dict['total'] = True

            # unpacks year values for the considered voice of entrate/spese
            for index, single_value in enumerate(main_value_set):
                single_value_deflated = float(single_value['valore'])*self.main_gdp_multiplier
                single_value_pc_deflated = float(single_value['valore_procapite'])*self.main_gdp_multiplier

                value_dict['series'].append([single_value['anno'], single_value_deflated])

                if single_value['anno'] == self.main_bilancio_year:
                    value_dict['value'] = round(single_value_deflated,0)
                    value_dict['procapite'] = single_value_pc_deflated

                    #calculate the % of variation between main_bilancio and comparison bilancio

                    variation = 0
                    if comp_not_available is False:
                        variation = self.calculate_variation(
                            single_value['valore'],
                            comp_values_regroup[main_value_denominazione]['valore'],
                        )

                    value_dict['variation'] = variation


            composition_data.append(value_dict)

        return composition_data


    def get_money_verb(self):
        e_money_verb = "previsti"
        s_money_verb = "previsti"

        if self.main_bilancio_type == "consuntivo":
            if self.cas_com_type == "cassa":
                e_money_verb = "riscossi"
                s_money_verb = "pagati"
            else:
                e_money_verb = "accertati"
                s_money_verb = "impegnati"

        return e_money_verb, s_money_verb

    # compose data dict for widget 4 : 1 box for voce detail
    def compose_widget_4(self):

            e_money_verb, s_money_verb = self.get_money_verb()

            return {
            "showHelp": self.show_help,
            "entrate": {
                "label": "entrate da",
                "sublabel": e_money_verb
            },
            "spese": {
                "label": "spese per",
                "sublabel": s_money_verb
            },
            "sublabel3": "sul {0} {1}".format(self.comp_bilancio_type, self.comp_bilancio_year)
            }

    # compose data dict for widget 5 : 2 box for voce detail

    def compose_widget_5(self,):
            return {
            "showHelp": self.show_help,

            "entrate": {
                "label": "Percentuale sul totale delle entrate"
            },
            "spese": {
                "label": "Percentuale sul totale delle spese"
                }
            }

    # compose data dict for widget 6 : 3 box for voce detail

    def compose_widget_6(self,):
            return {
            "showHelp": False,
            "entrate": {
                "label": "andamento entrate da"
            },
            "spese": {
                "label": "andamento spese per"
            },
            "sublabel3": "nei bilanci {0}".format(self.main_bilancio_type[:-1]+"i")
            }


    def get_context_data(self, **kwargs):

        widget1 = widget2 = widget3 = None
        context = super(BilancioCompositionWidgetView, self).get_context_data( **kwargs)

        ##
        # sets the correct template_name based on the type of rappresentation needed
        # gets the specified bilancio based on kwargs
        # identifies the bilancio to compare it with
        # creates the context to feed the Visup composition widget
        ##

        # composition data is the data struct to be passed to the context
        composition_data = {'hover': True, 'showLabels':False}

        consuntivo_slugs = {
            'entrate':{
                'cassa': 'consuntivo-entrate-cassa',
                'competenza': 'consuntivo-entrate-accertamenti',
            },
            'spese':{
                'cassa': 'consuntivo-spese-cassa-spese-correnti-funzioni',
                'competenza': 'consuntivo-spese-impegni-spese-correnti-funzioni',
            }
        }

        entrate_slug = {
            'preventivo': 'preventivo-entrate',
            'consuntivo': consuntivo_slugs['entrate'][self.cas_com_type]
        }

        spese_slug = {
            'preventivo': 'preventivo-spese-spese-correnti-funzioni',
            'consuntivo': consuntivo_slugs['spese'][self.cas_com_type]
        }

        composition_data['year'] = self.main_bilancio_year

        # identifies the bilancio for comparison

        self.comp_bilancio_type = 'preventivo'
        self.comp_bilancio_year = self.main_bilancio_year

        if self.main_bilancio_type == 'preventivo':
            self.comp_bilancio_type = 'consuntivo'
            self.comp_bilancio_year = self.main_bilancio_year-1

        self.main_gdp_deflator = settings.GDP_DEFLATORS[int(self.main_bilancio_year)]
        self.comp_gdb_deflator = settings.GDP_DEFLATORS[int(self.comp_bilancio_year)]

        if self.values_type == 'real':
            self.main_gdp_multiplier = self.main_gdp_deflator
            self.comp_gdp_multiplier = self.comp_gdb_deflator

        e_main_regroup, e_comp_regroup, e_widget_data =\
            self.get_data_set(
                main_bilancio_slug=entrate_slug[self.main_bilancio_type],
                comp_bilancio_slug=entrate_slug[self.comp_bilancio_type]
            )

        s_main_regroup, s_comp_regroup, s_widget_data =\
            self.get_data_set(
                main_bilancio_slug=spese_slug[self.main_bilancio_type],
                comp_bilancio_slug=spese_slug[self.comp_bilancio_type]
            )

        composition_data['entrate'] = e_widget_data
        composition_data['spese'] = s_widget_data


        widget1=widget2=widget3=None

        if self.main_bilancio_type == 'preventivo':

            # gets the entrate / spese total values from previous regrouping
            e_main_totale=[x for x in ifilter(lambda emt: emt['anno']==self.main_bilancio_year, e_main_regroup[self.totale_label])][0]
            s_main_totale=[x for x in ifilter(lambda smt: smt['anno']==self.main_bilancio_year, s_main_regroup[self.totale_label])][0]

            widget1 = {
                    "type": "bar",
                    "showHelp": self.show_help,
                    "label": "Entrate - Totale",
                    "sublabel2": "SUL consuntivo {0}".format(self.comp_bilancio_year),
                    "sublabel1": "",
                    "value": float(e_main_totale['valore'])*self.main_gdp_multiplier,
                    "procapite": float(e_main_totale['valore_procapite'])*self.main_gdp_multiplier,
                    "variation": self.calculate_variation(
                                    main_val=e_main_totale['valore'],
                                    comp_val=e_comp_regroup[self.totale_label]['valore'] if len(e_comp_regroup) else 0
                                      ),
                }

            widget2 = {
                    "type": "bar",
                    "showHelp": self.show_help,
                    "label": "Spese - Totale",
                    "sublabel2": "SUL consuntivo {0}".format(self.comp_bilancio_year),
                    "sublabel1": "",
                    "value": float(s_main_totale['valore'])*self.main_gdp_multiplier,
                    "procapite": float(s_main_totale['valore_procapite'])*self.main_gdp_multiplier,
                    "variation": self.calculate_variation(
                                    main_val=s_main_totale['valore'],
                                    comp_val=s_comp_regroup[self.totale_label]['valore'] if len(s_comp_regroup) else 0
                                  ),
                }

            widget3= {
                "type": "spark",
                "showHelp": self.show_help,
                "label": "Andamento nel tempo delle Entrate",
                "sublabel1": "",
                "sublabel3": "Entrate nei Bilanci Preventivi {0}-{1}".format(settings.APP_START_DATE.year, settings.APP_END_DATE.year),
                "series": [[v['anno'],v['valore']] for v in e_main_regroup[self.totale_label]]
                }

        else:

            # creates overview widget data for consuntivo cassa / competenza

            comp_preventivo_entrate  = comp_preventivo_spese = main_consuntivo_entrate = main_consuntivo_spese =None

            try:
                comp_preventivo_entrate = ValoreBilancio.objects.get(territorio=self.territorio, anno=self.comp_bilancio_year, voce__slug = 'preventivo-entrate')
                comp_preventivo_spese = ValoreBilancio.objects.get(territorio=self.territorio, anno=self.comp_bilancio_year, voce__slug = 'preventivo-spese')
                main_consuntivo_entrate = ValoreBilancio.objects.get(territorio=self.territorio, anno=self.comp_bilancio_year, voce__slug = entrate_slug[self.main_bilancio_type])
                main_consuntivo_spese = ValoreBilancio.objects.get(territorio=self.territorio, anno=self.comp_bilancio_year, voce__slug = spese_slug[self.main_bilancio_type])

            except ObjectDoesNotExist:
                pass
            else:
                # widget1
                # avanzo / disavanzo di cassa / competenza
                widget1 = {
                    "type": "surplus",
                    "showHelp": self.show_help,
                    "label": "Avanzo/disavanzo",
                    "sublabel1": "di "+self.cas_com_type,

                }

                yrs_to_consider = {
                    '1':self.main_bilancio_year-1,
                    '2':self.main_bilancio_year,
                    '3':self.main_bilancio_year+1
                }

                for k, year in yrs_to_consider.iteritems():

                    if settings.APP_START_DATE.year <= year <= settings.APP_END_DATE.year:

                        try:

                            entrate = ValoreBilancio.objects.get(anno=year, voce__slug=entrate_slug[self.main_bilancio_type], territorio=self.territorio).valore
                            spese = ValoreBilancio.objects.get(anno=year, voce__slug=spese_slug[self.main_bilancio_type], territorio=self.territorio).valore

                            if self.values_type == 'real':
                                entrate = float(entrate) *settings.GDP_DEFLATORS[year]
                                spese = float(spese) *settings.GDP_DEFLATORS[year]

                        except ObjectDoesNotExist:
                            continue
                        else:

                            widget1['year'+k] = year
                            widget1['value'+k] = entrate-spese


                # variations between consuntivo-entrate and preventivo-entrate / consuntivo-spese and preventivo-spese
                e_money_verb, s_money_verb = self.get_money_verb()
                widget2 = {
                    "type": "bar",
                    "showHelp": self.show_help,
                    "label": "Entrate - Totale",
                    "sublabel2": "SUL preventivo {0}".format(self.comp_bilancio_year),
                    "sublabel1": e_money_verb,
                    "value": float(main_consuntivo_entrate.valore)*self.main_gdp_multiplier,
                    "procapite": float(main_consuntivo_entrate.valore_procapite)*self.main_gdp_multiplier,
                    "variation": self.calculate_variation(
                                    main_val=main_consuntivo_entrate.valore,
                                    comp_val=comp_preventivo_entrate.valore,
                                  ),
                }

                widget3 = {
                    "type": "bar",
                    "showHelp": self.show_help,
                    "label": "Spese - Totale",
                    "sublabel2": "SUL preventivo {0}".format(self.comp_bilancio_year),
                    "sublabel1": s_money_verb,
                    "value": float(main_consuntivo_spese.valore)*self.main_gdp_multiplier,
                    "procapite": float(main_consuntivo_spese.valore_procapite)*self.main_gdp_multiplier,
                    "variation": self.calculate_variation(
                                    main_val=main_consuntivo_spese.valore,
                                    comp_val=comp_preventivo_spese.valore
                                  ),
                }




        # widget data
        composition_data['widget1']=widget1
        composition_data['widget2']=widget2
        composition_data['widget3']=widget3
        composition_data["widget4"]= self.compose_widget_4()
        composition_data["widget5"]= self.compose_widget_5()
        composition_data["widget6"]= self.compose_widget_6()
         # adds data to context
        context['composition_data']=json.dumps(composition_data)

        context['main_bilancio_type']=self.main_bilancio_type
        context['main_bilancio_year']=self.main_bilancio_year

        context['comparison_bilancio_type']=self.comp_bilancio_type
        context['comparison_bilancio_year']=self.comp_bilancio_year

        context['cas_com_type']=self.cas_com_type
        context['values_type']=self.values_type

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


class BilancioNotFoundView(LoginRequiredMixin, TemplateView):

    ##
    # show a page when a Comune doesnt have any bilancio
    ##

    template_name = "bilanci/bilancio_not_found.html"


class BilancioOverView(BilancioView):
    template_name = 'bilanci/bilancio_overview.html'
    selected_section = "bilancio"
    year = None
    tipo_bilancio = None
    values_type = None
    cas_com_type = None
    fun_int_view = None

    def get(self, request, *args, **kwargs):

        ##
        # if year or type parameter are missing redirects to a page for default year / default bilancio type
        ##

        must_redirect = False
        self.territorio = self.get_object()
        self.year = self.request.GET.get('year', settings.SELECTOR_DEFAULT_YEAR)
        self.tipo_bilancio = self.request.GET.get('type', settings.SELECTOR_DEFAULT_BILANCIO_TYPE)
        self.values_type = self.request.GET.get('values_type', 'real')
        self.cas_com_type = self.request.GET.get('cas_com_type', 'cassa')
        self.fun_int_view = self.request.GET.get('fun_int_view', 'funzioni')
        int_year = int(self.year)

        # if the request in the query string is incomplete the redirection will be used
        qs = self.request.META['QUERY_STRING']
        must_redirect = (len(qs.split('&')) < 4) or must_redirect

        ##
        # based on the type of bilancio and the selected section
        # the rootnode slug to check for existance is determined
        ##

        rootnode_slugs = {
            'preventivo': {
                'entrate':{
                    'cassa': 'preventivo-entrate',
                    'competenza': 'preventivo-entrate'
                },
                'spese':{
                    'cassa': 'preventivo-spese',
                    'competenza': 'preventivo-spese'
                },

            },
            'consuntivo': {
                'entrate':{
                    'cassa': 'consuntivo-entrate-cassa',
                    'competenza': 'consuntivo-entrate-accertamenti'
                },
                'spese': {
                    'cassa':'consuntivo-spese-cassa',
                    'competenza':'consuntivo-spese-impegni'
                }
            }
        }

        rootnode_slug = rootnode_slugs[self.tipo_bilancio]['entrate'][self.cas_com_type]
        if self.selected_section != 'bilancio':
            rootnode_slug = rootnode_slugs[self.tipo_bilancio][self.selected_section][self.cas_com_type]

        # best_bilancio determines based on the slug and the selected year
        # if that bilancio exists for that year
        # if it doesn't exist it returns the closest smaller year
        # in which that slug exists

        best_bilancio_year = self.territorio.best_year_voce(int_year, rootnode_slug)

        # if best_bilancio is None -> there is no bilancio in the db to show for the selected territorio
        if not best_bilancio_year:
            return HttpResponseRedirect(reverse('bilancio-not-found'))

        if str(best_bilancio_year) != self.year:
            must_redirect = True
            self.year = str(best_bilancio_year)


        if must_redirect:
            destination_view = 'bilanci-overview'

            if self.selected_section == 'entrate':
                destination_view = 'bilanci-entrate'
            elif self.selected_section == 'spese':
                destination_view = 'bilanci-spese'

            return HttpResponseRedirect(
                reverse(destination_view, kwargs={'slug':self.territorio.slug}) +\
                "?year={0}&type={1}&values_type={2}&cas_com_type={3}".\
                    format(
                        self.year,
                        self.tipo_bilancio,
                        self.values_type,
                        self.cas_com_type
                    )
            )

        return super(BilancioOverView, self).get(self, request, *args, **kwargs)


    def get_context_data(self, **kwargs ):

        context = super(BilancioOverView, self).get_context_data(**kwargs)
        
        query_string = self.request.META['QUERY_STRING']

        context['tipo_bilancio'] = self.tipo_bilancio
        context['selected_bilancio_type'] = self.tipo_bilancio

        menu_voices_kwargs = {'slug': self.territorio.slug}

        context['selected_section']=self.selected_section
        # get Comune context data from db
        context['comune_context'] = Contesto.get_context(int(self.year), self.territorio)
        context['territorio_opid'] = self.territorio.op_id
        context['query_string'] = query_string
        context['selected_year'] = self.year
        context['selector_default_year'] = settings.SELECTOR_DEFAULT_YEAR
        context['values_type'] = self.values_type
        context['cas_com_type'] = self.cas_com_type

        # identifies the bilancio for comparison

        comparison_bilancio_type = None
        main_bilancio_yr = int(self.year)
        if self.tipo_bilancio == 'preventivo':
            comparison_bilancio_type = 'consuntivo'
            comparison_bilancio_year = main_bilancio_yr-1
        else:
            comparison_bilancio_type = 'preventivo'
            comparison_bilancio_year = main_bilancio_yr

        context['comparison_bilancio_type']=comparison_bilancio_type
        context['comparison_bilancio_year']=comparison_bilancio_year

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

        context['comune_context'] = Contesto.get_context(int(year),self.territorio)
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
        context['bilancio_type'] = self.tipo_bilancio

        if self.tipo_bilancio == 'preventivo':
            context['bilancio_type_title'] = 'preventivi'
        else:
            context['bilancio_type_title'] = 'consuntivi'



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
        kwargs['anno'] = settings.CLASSIFICHE_END_YEAR

        try:
            url = reverse('classifiche-list', args=args , kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url

class ClassificheListView(LoginRequiredMixin, ListView):

    template_name = 'bilanci/classifiche.html'
    paginate_by = 15
    n_comuni = None
    parameter_type = None
    parameter = None
    anno = None
    anno_int = None
    reset_pages = False
    selected_regioni = []
    selected_cluster = []


    def get(self, request, *args, **kwargs):

        # checks that parameter type is correct
        # checks that parameter slug exists

        self.parameter_type = kwargs['parameter_type']
        parameter_slug = kwargs['parameter_slug']

        if self.parameter_type == 'indicatori':
            self.parameter = get_object_or_404(Indicatore, slug = parameter_slug)
        elif self.parameter_type == 'entrate' or self.parameter_type == 'spese':
            self.parameter = get_object_or_404(Voce, slug = parameter_slug)
        else:
            return reverse('404')

        self.anno = kwargs['anno']
        self.anno_int = int(self.anno)

        # if anno is out of range -> redirects to the latest yr for classifiche
        if self.anno_int > settings.CLASSIFICHE_END_YEAR or self.anno_int < settings.CLASSIFICHE_START_YEAR:
            return HttpResponseRedirect(reverse('classifiche-list',kwargs={'parameter_type':self.parameter_type , 'parameter_slug':self.parameter.slug,'anno':settings.CLASSIFICHE_END_YEAR}))

        # catches session variables if any
        if len(self.request.session.get('selected_regioni',[])):
            self.selected_regioni = [int(k) for k in self.request.session['selected_regioni']]
        if len(self.request.session.get('selected_cluster',[])):
            self.selected_cluster = self.request.session['selected_cluster']


        selected_regioni_get = [int(k) for k in self.request.GET.getlist('regione')]
        if len(selected_regioni_get):
            self.selected_regioni = selected_regioni_get


        selected_cluster_get = self.request.GET.getlist('cluster')
        if len(selected_cluster_get):
            self.selected_cluster = selected_cluster_get

        page = self.request.GET.getlist('page')
        if len(page):
            try:
                self.kwargs['page'] = int(page[0])
            except ValueError:
                pass


        return super(ClassificheListView, self).get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        # catches POST params and passes the execution to get method
        # if the params passed in POST are different then the parameter already set, then the page number return to 1
        selected_regione_post = [int(k) for k in self.request.POST.getlist('regione[]')]
        selected_cluster_post = self.request.POST.getlist('cluster[]')

        if len(selected_regione_post):
            if set(selected_regione_post) & set(self.selected_regioni) != len(self.selected_regioni):
                self.selected_regioni = selected_regione_post
                self.reset_pages = True

        if len(selected_cluster_post):
            if set(selected_cluster_post) & set(self.selected_cluster) != len(self.selected_cluster):
                self.selected_cluster = self.request.POST.getlist('cluster[]')
                self.reset_pages = True

        # sets session vars about what the user has selected
        self.request.session['selected_regioni'] = self.selected_regioni
        self.request.session['selected_cluster'] = self.selected_cluster

        # if the parameters have changed, redirects to page 1 for the new set
        if self.reset_pages:
            return HttpResponseRedirect(reverse('classifiche-list', kwargs=kwargs))

        return self.get(request, *args, **kwargs)

    def get_queryset(self):

        # construct the queryset based on the type of parameter (voce/indicatore) and
        # the comparison set on which the variation will be computed

        if self.parameter_type == 'indicatori':
            base_queryset = ValoreIndicatore.objects.filter(indicatore = self.parameter).order_by('-valore')

        else:
            base_queryset = ValoreBilancio.objects.filter(voce = self.parameter).order_by('-valore_procapite')


        ##
        # Filters on regioni / cluster
        ##

        # initial territori_baseset is the complete list of comuni
        territori_baseset = Territorio.objects.filter(territorio=Territorio.TERRITORIO.C)

        if len(self.selected_regioni):
            # this passege is necessary because in the regione field of territorio there is the name of the region
            selected_regioni_names = list(Territorio.objects.\
                filter(pk__in=self.selected_regioni, territorio=Territorio.TERRITORIO.R).values_list('denominazione',flat=True))

            territori_baseset = territori_baseset.filter(regione__in=selected_regioni_names)


        if len(self.selected_cluster):
            territori_baseset = territori_baseset.filter(cluster__in=self.selected_cluster)


        self.queryset =  base_queryset.\
                        filter( territorio__territorio = 'C', anno = self.anno, territorio__in=territori_baseset).select_related('territorio')


        return self.queryset

    def get_context_data(self, **kwargs):

        # enrich the Queryset in object_list with Political context data and variation value
        object_list = []
        ordinal_position = 1
        comparison_year = self.anno_int - 1
        all_regions = Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).values_list('pk',flat=True)
        all_clusters = Territorio.objects.filter(territorio=Territorio.TERRITORIO.C).values_list('cluster',flat=True)

        context = super(ClassificheListView, self).get_context_data( **kwargs)

        # creates context data based on the paginated queryset
        paginated_queryset = context['object_list']
        queryset_territori = list(paginated_queryset.values_list('territorio',flat=True))


        # create comparison set to calculate variation from last yr
        if self.parameter_type == 'indicatori':

            comparison_set = list(ValoreBilancio.objects.\
                                filter(territorio__in = queryset_territori, anno = comparison_year).select_related('territorio').\
                                values('valore','territorio__pk','territorio__denominazione'))
        else:

            comparison_set = list(ValoreBilancio.objects.\
                                filter(territorio__in = queryset_territori, anno = comparison_year).select_related('territorio').\
                                values('valore_procapite','territorio__pk','territorio__denominazione'))

        self.n_comuni = self.queryset.count()

        # regroups incarichi politici based on territorio

        incarichi_set = Incarico.get_incarichi_attivi_set(queryset_territori, self.anno).select_related('territorio')
        incarichi_territorio_keygen = lambda x: x.territorio.pk
        incarichi_regroup = dict((k,list(v)) for k,v in groupby(incarichi_set, key=incarichi_territorio_keygen))

        # regroups comparison values based on territorio
        regroup_territorio_keygen = lambda x: x['territorio__pk']
        comparison_regroup = dict((k,list(v)[0]) for k,v in groupby(comparison_set, key=regroup_territorio_keygen))



        for valoreObj in paginated_queryset:
            valore_template = None
            incarichi = []
            comparison_value=0
            variazione = 0

            if self.parameter_type =='indicatori':
                valore_template = valoreObj.valore
                comparison_value = comparison_regroup.get(valoreObj.territorio.pk,{}).get('valore',None)

            else:
                valore_template = valoreObj.valore_procapite
                comparison_value = comparison_regroup.get(valoreObj.territorio.pk,{}).get('valore_procapite',None)


            if comparison_value is not None:
                variazione = valore_template - comparison_value

            if valoreObj.territorio.pk in incarichi_regroup.keys():
                incarichi = incarichi_regroup[valoreObj.territorio.pk]

            territorio_dict = {
                'territorio':{
                    'denominazione': valoreObj.territorio.denominazione,
                    'prov': valoreObj.territorio.prov,
                    'regione': valoreObj.territorio.regione,
                    'pk': valoreObj.territorio.pk,
                    },
                'valore': valore_template,
                'incarichi_attivi': incarichi,
                'variazione':variazione,
                'position': ordinal_position
                }

            ordinal_position+=1

            object_list.append( territorio_dict )


        # updates obj list
        context['object_list'] = object_list
        context['n_comuni'] = self.n_comuni

        # defines the lists of possible confrontation parameters
        context['selected_par_type'] = self.parameter_type
        context['selected_parameter'] = self.parameter
        context['selected_regioni'] = self.selected_regioni if len(self.selected_regioni)>0 else all_regions
        context['selected_cluster'] = self.selected_cluster if len(self.selected_cluster)>0 else all_clusters

        context['selected_year'] = self.anno
        context['selector_default_year'] = settings.CLASSIFICHE_END_YEAR
        context['selector_start_year'] = settings.CLASSIFICHE_START_YEAR
        context['selector_end_year'] = settings.CLASSIFICHE_END_YEAR

        context['indicator_list'] = Indicatore.objects.all().order_by('denominazione')
        context['entrate_list'] = Voce.objects.get(slug='consuntivo-entrate-cassa').get_children().order_by('slug')
        context['spese_list'] = Voce.objects.get(slug='consuntivo-spese-cassa-spese-somma-funzioni').get_children().order_by('slug')

        context['regioni_list'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).order_by('denominazione')
        context['cluster_list'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.L).order_by('-cluster')

        # creates url for share button
        regioni_list=['',]
        regioni_list.extend([str(r) for r in self.selected_regioni])
        cluster_list=['',]
        cluster_list.extend(self.selected_cluster)
        # gets current page url
        long_url = self.request.build_absolute_uri(
            reverse('classifiche-list', kwargs={'anno':self.anno,'parameter_type':self.parameter_type, 'parameter_slug':self.parameter.slug})
            )+'?' + "&regione=".join(regioni_list)+"&cluster=".join(cluster_list)+'&page='+str(context['page_obj'].number)


        # checks if short url is already in the db, otherwise asks to google to shorten the url

        short_url_obj=None
        try:
            short_url_obj = ShortUrl.objects.get(long_url = long_url)

        except ObjectDoesNotExist:

            payload = { 'longUrl': long_url+'&key='+settings.GOOGLE_SHORTENER_API_KEY }
            headers = { 'content-type': 'application/json' }
            short_url_req = requests.post(settings.GOOGLE_SHORTENER_URL, data=json.dumps(payload), headers=headers)
            if short_url_req.status_code == requests.codes.ok:
                short_url = short_url_req.json().get('id')
                short_url_obj = ShortUrl()
                short_url_obj.short_url = short_url
                short_url_obj.long_url = long_url
                short_url_obj.save()

        if short_url_obj:
            context['share_url'] = short_url_obj.short_url

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


