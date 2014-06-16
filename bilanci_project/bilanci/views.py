from itertools import groupby, ifilter, repeat
from operator import itemgetter
import os
import re
import json
from django.core.cache import cache
import feedparser
import zmq
import requests
from collections import OrderedDict

from requests.exceptions import ConnectionError, Timeout, SSLError, ProxyError

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView, View, ListView
from django.conf import settings
from bilanci.forms import TerritoriComparisonSearchForm, EarlyBirdForm, TerritoriSearchFormHome, TerritoriSearchFormClassifiche
from bilanci.managers import ValoriManager
from bilanci.models import ValoreBilancio, Voce, Indicatore, ValoreIndicatore
from shorturls.models import ShortUrl
from django.http.response import HttpResponse, HttpResponseRedirect, Http404
from bilanci.utils import couch

from territori.models import Territorio, Contesto, Incarico


class ShareUrlMixin(object):
    share_url = None

    def get(self, request, *args, **kwargs):

        # gets current page url
        long_url = "http://"+request.META['HTTP_HOST']+request.get_full_path()

        if len(long_url) < 80:
            self.share_url = long_url

        else:
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
                self.share_url = short_url_obj.short_url

        return super(ShareUrlMixin, self).get(request, *args, **kwargs)


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data( **kwargs)
        context['territori_search_form_home'] = TerritoriSearchFormHome()
        op_blog_posts = cache.get('blog-posts')
        if op_blog_posts is None:
            op_blog_posts = feedparser.parse('http://blog.openpolis.it/categorie/%s/feed/' % settings.OP_BLOG_CATEGORY).entries[:3]
            cache.set('blog-posts', op_blog_posts)
        context['op_blog_posts'] = op_blog_posts
        return context


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
                # sets incarico marker color and highlight
                'icon': settings.INCARICO_MARKER_DUMMY,
                'color': settings.INCARICO_MARKER_INACTIVE,
                'highlightColor': highlight_color,
            }

            # truncates date start to timeline start
            timeline_start_date = settings.TIMELINE_START_DATE.date()
            timeline_end_date = settings.TIMELINE_END_DATE.date()

            if incarico.data_inizio < timeline_start_date:
                dict_widget['start'] = timeline_start_date.strftime(self.date_fmt)
            else:
                dict_widget['start'] = incarico.data_inizio.strftime(self.date_fmt)


            if incarico.data_fine:
                dict_widget['end'] = incarico.data_fine.strftime(self.date_fmt)
            else:
                dict_widget['end'] = timeline_end_date.strftime(self.date_fmt)

            if incarico.pic_url:
                dict_widget['icon'] = incarico.pic_url

            if incarico.tipologia == Incarico.TIPOLOGIA.commissario:
                # commissari
                dict_widget['label'] = "Commissario".title()
                dict_widget['icon'] = settings.INCARICO_MARKER_COMMISSARIO
                dict_widget['sublabel'] = incarico.motivo_commissariamento.title()

            else:

                # sets sindaco / vicesindaco name, surname
                dict_widget['label'] = "{0}".\
                    format(

                        incarico.cognome.title().encode('utf-8'),
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
        transformed_set =  self.transform_incarichi(incarichi_set, highlight_color)

        if len(transformed_set):
            return [transformed_set]
        else:
            return None


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


        legend = {
            'title':None,

             "items":[
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
        }



        return HttpResponse(
            content=json.dumps(
                {
                    "timeSpans":incarichi_set,
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
                    "timeSpans":incarichi_set,
                    'data':indicatori_set,
                    'legend':{'title':None, 'items':legend_set}
                }
            ),
            content_type="application/json"
        )


# calculatevariationsmixin
# includes function to calculate voce variations over the years

class CalculateVariationsMixin(object):

    somma_funzioni_affix = '-spese-somma-funzioni'
    main_gdp_deflator = comp_gdb_deflator = None
    main_gdp_multiplier = comp_gdp_multiplier = 1.0


    # calculates the % variation of main_value compared to comparison_values
    # adjusting the values with gdp deflator if needed

    def calculate_variation(self, main_val, comp_val, ):

        if main_val is None or comp_val is None:
            return None

        deflated_main_val = float(main_val) * self.main_gdp_multiplier
        deflated_comp_val = float(comp_val) * self.comp_gdp_multiplier

        if deflated_comp_val != 0 and deflated_main_val != 0:
            # sets 2 digit precision for variation after decimal point
            return round(((deflated_main_val-deflated_comp_val)/ deflated_comp_val)*100.0,2)
        else:
            # value passes from 0 to N:
            # variation would be infinite so variation is set to null
            return None



    def get_slugset_entrate(self, bilancio_type, cas_com_type, widget_type="overview", include_totale = True):
        slugset = []
        ##
        # overview widget
        ##
        if widget_type == 'overview':
            if bilancio_type == "preventivo":
                rootnode_slug = "preventivo-entrate"
                totale_slug = rootnode_slug
            else:
                if cas_com_type == 'cassa':
                    rootnode_slug = totale_slug = 'consuntivo-entrate-cassa'
                else:
                    rootnode_slug = totale_slug = 'consuntivo-entrate-accertamenti'

            rootnode = Voce.objects.get(slug=rootnode_slug)
            slugset = list(rootnode.get_children().order_by('slug').values_list('slug',flat=True))

        ##
        # entrate widget
        ##
        else:
            if bilancio_type == "preventivo":
                rootnode_slug = totale_slug = 'preventivo-entrate'
                rootnode = Voce.objects.get(slug=rootnode_slug)
                # gets 1 and 2nd level descendants from root
                slugset = list(rootnode.get_descendants(include_self=False).filter(level__lte=rootnode.level+2).values_list('slug', flat=True))

            else:

                if cas_com_type == 'cassa':
                    rootnode_slug = totale_slug = 'consuntivo-entrate-cassa'
                else:
                    rootnode_slug = totale_slug = 'consuntivo-entrate-accertamenti'

                rootnode = Voce.objects.get(slug=rootnode_slug)

                # gets 1 and 2nd level descendants from root
                slugset = list(rootnode.get_descendants(include_self=False).filter(level__lte=rootnode.level+2).values_list('slug', flat=True))

        if include_totale:
            slugset.append(totale_slug)

        return slugset, totale_slug


    def get_slugset_spese(self, bilancio_type, cas_com_type, include_totale=True):

        ##
        # overview widget and spese widget
        ##

        if bilancio_type == "preventivo":
            totale_slug = "preventivo-spese"
            rootnode_slug = totale_slug+self.somma_funzioni_affix
        else:
            if cas_com_type == 'cassa':
                totale_slug = bilancio_type+'-spese-cassa'
            else:
                totale_slug = bilancio_type+'-spese-impegni'

            rootnode_slug = totale_slug+self.somma_funzioni_affix

        rootnode = Voce.objects.get(slug = rootnode_slug)
        slugset = list(rootnode.get_children().values_list('slug', flat=True))
        slugset.append(totale_slug+'-prestiti')
        slugset.append(totale_slug+'-spese-per-conto-terzi')

        if include_totale:
            slugset.append(totale_slug)

        return slugset, totale_slug



class BilancioCompositionWidgetView(CalculateVariationsMixin, TemplateView):

    template_name = None
    show_help = False
    totale_label = "Totale"
    territorio = None
    serie_start_year = settings.TIMELINE_START_DATE.year
    serie_end_year = settings.TIMELINE_END_DATE.year
    widget_type = None
    main_gdp_deflator = comp_gdb_deflator = None
    main_gdp_multiplier = comp_gdp_multiplier = 1.0
    main_bilancio_year = main_bilancio_type = None
    comp_bilancio_year = comp_bilancio_type = None
    comparison_not_available = False
    values_type = None
    cas_com_type = None


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


    def calc_variations_set(self, main_dict, comp_dict,):
        # creates a variations dict based on voce denominazione
        variations = {}
        for main_denominazione, main_value_set in main_dict.iteritems():
            for main_value_dict in main_value_set:
                if main_value_dict['anno'] == self.main_bilancio_year:

                    main_value = main_value_dict['valore']

                    #  gets comparison value for the same voce
                    # checks also for voce with denominazione followed by space: bug

                    main_denominazione_strip = main_denominazione.strip()
                    comparison_value_dict = comp_dict.get(main_denominazione_strip,{})
                    if comparison_value_dict == {}:
                        comparison_value_dict = comp_dict.get(main_denominazione_strip+" ",{})

                    comparison_value_dict = comp_dict.get(main_denominazione,{})

                    comparison_value = comparison_value_dict.get('valore',None)

                    variations[main_denominazione] =\
                        self.calculate_variation(
                            main_value,
                            comparison_value)

        return variations


    def get(self, request, *args, **kwargs):

        ##
        # get params from GET
        # identifies territorio, bilancio yr, bilancio type for main bilancio
        # calculates the best comparison yr and comparison bilancio type
        # set gdp deflator / multiplier for selected yrs
        # set the right template based on widget type
        ##

        self.values_type = self.request.GET.get('values_type', 'real')
        self.cas_com_type = self.request.GET.get('cas_com_type', 'cassa')
        self.main_bilancio_year = int(kwargs.get('bilancio_year', settings.APP_END_DATE.year ))
        self.main_bilancio_type = kwargs.get('bilancio_type','consuntivo')
        self.widget_type = kwargs.get('widget_type', 'overview')
        territorio_slug = kwargs.get('territorio_slug', None)

        if not territorio_slug:
            return reverse('404')

        self.territorio = get_object_or_404(Territorio, slug = territorio_slug)

        # identifies the bilancio for comparison


        if self.main_bilancio_type == 'preventivo':

            self.comp_bilancio_type = 'consuntivo'
            self.cas_com_type = "cassa"
            verification_voice = self.comp_bilancio_type+'-entrate'
            self.comp_bilancio_year = self.territorio.best_year_voce(year=self.main_bilancio_year-1, slug = verification_voice)
        else:
            self.comp_bilancio_type = 'preventivo'
            verification_voice = self.comp_bilancio_type+'-entrate'
            self.comp_bilancio_year = self.territorio.best_year_voce(year=self.main_bilancio_year, slug = verification_voice )


        if self.comp_bilancio_year is None:
            self.comparison_not_available = True

        # sets current gdp deflator
        self.main_gdp_deflator = settings.GDP_DEFLATORS[int(self.main_bilancio_year)]

        if not self.comparison_not_available:
            self.comp_gdb_deflator = settings.GDP_DEFLATORS[int(self.comp_bilancio_year)]

        if self.values_type == 'real':
            self.main_gdp_multiplier = self.main_gdp_deflator
            if not self.comparison_not_available:
                self.comp_gdp_multiplier = self.comp_gdb_deflator


        if self.widget_type == 'overview':
            self.template_name = 'bilanci/composizione_bilancio.html'

        elif self.widget_type == 'entrate' or self.widget_type =='spese':
            self.template_name = 'bilanci/composizione_entrate_uscite.html'
        else:
            return reverse('404')

        return super(BilancioCompositionWidgetView, self).get(self, request, *args, **kwargs)



    # return data_regroup for main bilancio over app years
    def get_main_data(self, slugset, totale_slug):

        values = ValoreBilancio.objects.filter(
            voce__slug__in= slugset,
            anno__gte=self.serie_start_year,
            anno__lte=self.serie_end_year,
            territorio=self.territorio
            ).values(
                'voce__pk',
                'voce__parent__pk',
                'voce__parent__parent__pk',
                'voce__denominazione',
                'voce__level',
                'anno',
                'valore',
                'valore_procapite',
                'voce__slug').order_by('voce__denominazione','anno')

        main_keygen = lambda x: self.totale_label if x['voce__slug'] == totale_slug else x['voce__denominazione'].strip()
        main_values_regroup = dict((k,list(v)) for k,v in groupby(values, key=main_keygen))

        return main_values_regroup


    # return data_regroup for comp bilancio for comparison year
    def get_comp_data(self, slugset, totale_slug):

        values = ValoreBilancio.objects.filter(
            voce__slug__in=slugset,
            anno = self.comp_bilancio_year,
            territorio=self.territorio
        ).values('voce__denominazione', 'voce__level', 'anno','valore','valore_procapite','voce__slug').order_by('voce__denominazione','anno')

        comp_keygen = lambda x: self.totale_label if x['voce__slug'] == totale_slug else x['voce__denominazione'].strip()
        comp_values_regroup = dict((k,list(v)[0]) for k,v in groupby(values, key=comp_keygen))

        return comp_values_regroup


    def compose_overview_data(self, main_values_regroup, variations):
        composition_data = []

        ##
        # compose_overview_data
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

                    #insert the % of variation between main_bilancio and comparison bilancio
                    value_dict['variation'] = variations[main_value_denominazione]


            composition_data.append(value_dict)

        return composition_data




    def compose_partial_data(self, main_values_regroup, variations, totale_level,):
        composition_data = []

        ##
        # compose_overview_data
        # loops over the results to create the data struct to be returned
        ##
        for main_value_denominazione, main_value_set in main_values_regroup.iteritems():

            # creates value dict
            value_dict = dict(label = main_value_denominazione, series = [], total = False)

            # insert hierarchy info into the data struct

            # if diff is same level as totale
            if main_value_denominazione != self.totale_label:
                sample_obj = main_value_set[0]

                diff = sample_obj['voce__level']-totale_level-1

                # if the voce belongs to somma-funzioni branch then it should
                # be considered one level less than its real level

                if self.somma_funzioni_affix  in sample_obj['voce__slug']:
                    diff -= 1

                if diff == 0:
                    value_dict['layer1'] = sample_obj['voce__pk']

                elif diff == 1:
                    value_dict['layer1'] = sample_obj['voce__parent__pk']
                    value_dict['layer2'] = sample_obj['voce__pk']

                elif diff == 2:
                    value_dict['layer1'] = sample_obj['voce__parent__parent__pk']
                    value_dict['layer2'] = sample_obj['voce__parent__pk']
                    value_dict['layer3'] = sample_obj['voce__pk']

                #     sets the value to mark the circle as a parent of other voce or not
                voce = Voce.objects.get(pk=sample_obj['voce__pk'])
                value_dict['is_parent'] = not voce.is_leaf_node()


            value_dict['andamento']=0
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

                    #insert the % of variation between main_bilancio and comparison bilancio
                    value_dict['variation'] = variations[main_value_denominazione]
                    value_dict["variationAbs"] = variations[main_value_denominazione]
                    value_dict["andamento"] = 1


            composition_data.append(value_dict)

        return composition_data

    def create_context_entrate(self):

        context = {}
        context["type"]= "ENTRATE"
        # entrate data
        main_ss_e , main_tot_e = self.get_slugset_entrate(self.main_bilancio_type,self.cas_com_type, self.widget_type)
        comp_ss_e, comp_tot_e = self.get_slugset_entrate(self.comp_bilancio_type,self.cas_com_type, self.widget_type)
        main_ss_s, main_tot_s = self.get_slugset_spese(self.main_bilancio_type, self.cas_com_type)
        totale_level = Voce.objects.get(slug=main_tot_e).level
        main_regroup_e = self.get_main_data(main_ss_e, main_tot_e)
        main_regroup_s = self.get_main_data(main_ss_s, main_tot_s)
        comp_regroup_e = self.get_comp_data(comp_ss_e, comp_tot_e)
        comp_ss_s, comp_tot_s = self.get_slugset_spese(self.comp_bilancio_type,self.cas_com_type)
        comp_regroup_s = self.get_comp_data(comp_ss_s, comp_tot_s)
        variations_e = self.calc_variations_set(main_regroup_e, comp_regroup_e,)
        context['composition'] = json.dumps(self.compose_partial_data(main_regroup_e, variations_e, totale_level))
        s_main_totale=[x for x in ifilter(lambda smt: smt['anno']==self.main_bilancio_year, main_regroup_s[self.totale_label])][0]
        e_main_totale=[x for x in ifilter(lambda emt: emt['anno']==self.main_bilancio_year, main_regroup_e[self.totale_label])][0]

        # widget1 : bar totale entrate
        context["w1_type"]= "bar"
        context["w1_label"]= "Entrate - Totale"
        context["w1_sublabel2"]= "SUL consuntivo {0}".format(self.comp_bilancio_year)
        context["w1_sublabel1"]= ""
        context["w1_value"]= float(e_main_totale['valore'])*self.main_gdp_multiplier
        context["w1_value_procapite"]= float(e_main_totale['valore_procapite'])*self.main_gdp_multiplier
        if not self.comparison_not_available:

            context["w1_variation"]= self.calculate_variation(
                                main_val=e_main_totale['valore'],
                                comp_val=comp_regroup_e[self.totale_label]['valore'] if len(comp_regroup_e) else 0
                            )

        # widget2: bar totale spese
        context["w2_type"]= "bar"
        context["w2_label"]= "Spese - Totale"
        context["w2_sublabel2"]= "SUL consuntivo {0}".format(self.comp_bilancio_year)
        context["w2_sublabel1"]= ""
        context["w2_value"]= float(s_main_totale['valore'])*self.main_gdp_multiplier
        context["w2_value_procapite"]= float(s_main_totale['valore_procapite'])*self.main_gdp_multiplier
        if not self.comparison_not_available:

            context["w2_variation"]= self.calculate_variation(
                                main_val=s_main_totale['valore'],
                                comp_val=comp_regroup_s[self.totale_label]['valore'] if len(comp_regroup_s) else 0
                            )

        # widget3: andamento nel tempo del totale delle entrate
        context["w3_type"]= "spark"
        context["w3_label"]=  "Andamento nel tempo delle Entrate"
        context["w3_sublabel1"]= ''
        context["w3_sublabel2"]= ''
        context["w3_sublabel3"]= "Entrate nei Bilanci {0} {1}-{2}".format(self.main_bilancio_type[:-1]+"i",settings.APP_START_DATE.year, settings.APP_END_DATE.year)
        context['w3_series'] = json.dumps([[v['anno'],v['valore']] for v in main_regroup_e[self.totale_label]])

        context["w1_showhelp"] = context["w2_showhelp"] = context["w3_showhelp"] = context["w4_showhelp"] = context["w5_showhelp"] = context["w6_showhelp"] = self.show_help
        context["w4_e_moneyverb"], context["w4_s_moneyverb"] = self.get_money_verb()
        context["w6_main_bilancio_type_plural"]= self.main_bilancio_type[:-1]+"i"
        context['active_layers'] = 2

        return context



    def create_context_spese(self):

        context = {}
        context["type"]= "SPESE"
        # spese data
        main_ss_e , main_tot_e = self.get_slugset_entrate(self.main_bilancio_type,self.cas_com_type, self.widget_type)
        main_ss_s, main_tot_s = self.get_slugset_spese(self.main_bilancio_type, self.cas_com_type)
        main_regroup_e = self.get_main_data(main_ss_e, main_tot_e)
        comp_ss_s, comp_tot_s = self.get_slugset_spese(self.comp_bilancio_type,self.cas_com_type)
        totale_level = Voce.objects.get(slug=main_tot_s).level
        main_regroup_s = self.get_main_data(main_ss_s, main_tot_s)
        comp_regroup_s = self.get_comp_data(comp_ss_s, comp_tot_s)
        comp_ss_e, comp_tot_e = self.get_slugset_entrate(self.comp_bilancio_type,self.cas_com_type, self.widget_type)
        comp_regroup_e = self.get_comp_data(comp_ss_e, comp_tot_e)
        variations_s = self.calc_variations_set(main_regroup_s, comp_regroup_s,)
        context['composition'] = json.dumps(self.compose_partial_data(main_regroup_s, variations_s, totale_level))
        s_main_totale=[x for x in ifilter(lambda smt: smt['anno']==self.main_bilancio_year, main_regroup_s[self.totale_label])][0]
        e_main_totale=[x for x in ifilter(lambda emt: emt['anno']==self.main_bilancio_year, main_regroup_e[self.totale_label])][0]

        #  # widget1 : bar totale spese
        context["w1_type"]= "bar"
        context["w1_label"]= "Spese - Totale"
        context["w1_sublabel2"]= "SUL consuntivo {0}".format(self.comp_bilancio_year)
        context["w1_sublabel1"]= ""
        context["w1_value"]= float(s_main_totale['valore'])*self.main_gdp_multiplier
        context["w1_value_procapite"]= float(s_main_totale['valore_procapite'])*self.main_gdp_multiplier
        if not self.comparison_not_available:

            context["w1_variation"]= self.calculate_variation(
                                main_val=s_main_totale['valore'],
                                comp_val=comp_regroup_s[self.totale_label]['valore'] if len(comp_regroup_s) else 0
                            )
        # # widget2: bar totale entrate
        
        context["w2_type"]= "bar"
        context["w2_label"]= "Entrate - Totale"
        context["w2_sublabel2"]= "SUL consuntivo {0}".format(self.comp_bilancio_year)
        context["w2_sublabel1"]= ""
        context["w2_value"]= float(e_main_totale['valore'])*self.main_gdp_multiplier
        context["w2_value_procapite"]= float(e_main_totale['valore_procapite'])*self.main_gdp_multiplier
        if not self.comparison_not_available:

            context["w2_variation"]= self.calculate_variation(
                                main_val=e_main_totale['valore'],
                                comp_val=comp_regroup_e[self.totale_label]['valore'] if len(comp_regroup_e) else 0
                            )
        

        # widget3: andamento nel tempo del totale delle entrate
        context["w3_type"]= "spark"
        context["w3_label"]=  "Andamento nel tempo delle Spese"
        context["w3_sublabel1"]= ''
        context["w3_sublabel2"]= ''
        context["w3_sublabel3"]= "Entrate nei Bilanci {0} {1}-{2}".format(self.main_bilancio_type[:-1]+"i",settings.APP_START_DATE.year, settings.APP_END_DATE.year)
        context['w3_series'] = json.dumps([[v['anno'],v['valore']] for v in main_regroup_s[self.totale_label]])

        context["w1_showhelp"] = context["w2_showhelp"] = context["w3_showhelp"] = context["w4_showhelp"] = context["w5_showhelp"] = context["w6_showhelp"] = self.show_help
        context["w4_e_moneyverb"], context["w4_s_moneyverb"] = self.get_money_verb()
        context["w6_main_bilancio_type_plural"]= self.main_bilancio_type[:-1]+"i"
        context['active_layers'] = 1

        return context


    def create_context_overview(self):

        context = {}
        # entrate data
        main_ss_e , main_tot_e = self.get_slugset_entrate(self.main_bilancio_type,self.cas_com_type, self.widget_type)
        comp_ss_e, comp_tot_e = self.get_slugset_entrate(self.comp_bilancio_type,self.cas_com_type, self.widget_type)
        main_regroup_e = self.get_main_data(main_ss_e, main_tot_e)
        comp_regroup_e = self.get_comp_data(comp_ss_e, comp_tot_e)
        variations_e = self.calc_variations_set(main_regroup_e, comp_regroup_e)

        # spese data
        main_ss_s, main_tot_s = self.get_slugset_spese(self.main_bilancio_type, self.cas_com_type)
        comp_ss_s, comp_tot_s = self.get_slugset_spese(self.comp_bilancio_type, self.cas_com_type)
        main_regroup_s = self.get_main_data(main_ss_s, main_tot_s)
        comp_regroup_s = self.get_comp_data(comp_ss_s, comp_tot_s)
        variations_s = self.calc_variations_set(main_regroup_s, comp_regroup_s,)


        context['entrate'] = json.dumps(self.compose_overview_data(main_regroup_e, variations_e))
        context['spese'] = json.dumps(self.compose_overview_data(main_regroup_s, variations_s))

        if self.main_bilancio_type == 'preventivo':

            # gets the entrate / spese total values from previous regrouping
            e_main_totale=[x for x in ifilter(lambda emt: emt['anno']==self.main_bilancio_year, main_regroup_e[self.totale_label])][0]
            s_main_totale=[x for x in ifilter(lambda smt: smt['anno']==self.main_bilancio_year, main_regroup_s[self.totale_label])][0]

            context["w1_type"]= "bar"
            context["w1_label"]= "Entrate - Totale"
            context["w1_sublabel2"]= "SUL consuntivo {0}".format(self.comp_bilancio_year)
            context["w1_sublabel1"]= ""
            context["w1_value"]= float(e_main_totale['valore'])*self.main_gdp_multiplier
            context["w1_value_procapite"]= float(e_main_totale['valore_procapite'])*self.main_gdp_multiplier

            context['w2_label']  =  "Spese - Totale"
            context['w2_sublabel1'] = ""
            context['w2_sublabel2'] = "consuntivo {0}".format(self.comp_bilancio_year)
            context['w2_value'] = float(s_main_totale['valore'])*self.main_gdp_multiplier
            context['w2_value_procapite'] = float(s_main_totale['valore_procapite'])*self.main_gdp_multiplier
            if not self.comparison_not_available:

                context["w1_variation"]= self.calculate_variation(
                                    main_val=e_main_totale['valore'],
                                    comp_val=comp_regroup_e[self.totale_label]['valore'] if len(comp_regroup_e) else 0
                                )


                context['w2_variation'] =\
                    self.calculate_variation(
                        main_val=s_main_totale['valore'],
                        comp_val=comp_regroup_s[self.totale_label]['valore'] if len(comp_regroup_s) else 0
                      )

            context["w3_type"]= "spark"
            context["w3_label"]=  "Andamento nel tempo delle Entrate"
            context["w3_sublabel1"]= ''
            context["w3_sublabel2"]= ''
            context["w3_sublabel3"]= "Entrate nei Bilanci Preventivi {0}-{1}".format(settings.APP_START_DATE.year, settings.APP_END_DATE.year)
            context['w3_series'] = json.dumps([[v['anno'],v['valore']] for v in main_regroup_e[self.totale_label]])

        else:

            # # creates overview widget data for consuntivo cassa / competenza

            main_consuntivo_entrate = [x for x in ifilter(lambda emt: emt['anno']==self.main_bilancio_year, main_regroup_e[self.totale_label])][0]
            main_consuntivo_spese= [x for x in ifilter(lambda emt: emt['anno']==self.main_bilancio_year, main_regroup_s[self.totale_label])][0]

            # widget1
            # avanzo / disavanzo di cassa / competenza
            yrs_to_consider = { '1':self.main_bilancio_year-1,'2':self.main_bilancio_year,'3':self.main_bilancio_year+1}

            for k, year in yrs_to_consider.iteritems():
                if settings.APP_START_DATE.year <= year <= settings.APP_END_DATE.year:
                    try:
                        entrate = ValoreBilancio.objects.get(anno=year, voce__slug=main_tot_e, territorio=self.territorio).valore
                        spese = ValoreBilancio.objects.get(anno=year, voce__slug=main_tot_s, territorio=self.territorio).valore

                        if self.values_type == 'real':
                            entrate = float(entrate) *settings.GDP_DEFLATORS[year]
                            spese = float(spese) *settings.GDP_DEFLATORS[year]

                    except ObjectDoesNotExist:
                        continue
                    else:
                        context['w1_year'+k] = year
                        context['w1_value'+k] = entrate-spese


            context["w1_type"]= "surplus"
            context["w1_label"]= "Avanzo/disavanzo"
            context["w1_sublabel1"]= "di "+self.cas_com_type
            context["w1_sublabel2"]= ""

            # variations between consuntivo-entrate and preventivo-entrate / consuntivo-spese and preventivo-spese
            e_money_verb, s_money_verb = self.get_money_verb()

            context['w2_label']  =  "Entrate - Totale"
            context['w2_sublabel1'] = e_money_verb
            context['w2_sublabel2'] = "preventivo {0}".format(self.comp_bilancio_year)
            context['w2_value'] = float(main_consuntivo_entrate['valore'])*self.main_gdp_multiplier
            context['w2_value_procapite'] = float(main_consuntivo_entrate['valore_procapite'])*self.main_gdp_multiplier


            context["w3_type"]= "bar"
            context["w3_label"]=  "Spese - Totale"
            context["w3_sublabel1"]= s_money_verb
            context["w3_sublabel2"]= "SUL preventivo {0}".format(self.comp_bilancio_year)

            context['w3_value'] = float(main_consuntivo_spese['valore'])*self.main_gdp_multiplier
            context['w3_value_procapite'] = float(main_consuntivo_spese['valore_procapite'])*self.main_gdp_multiplier


            if not self.comparison_not_available:

                comp_preventivo_entrate = comp_regroup_e[self.totale_label]
                comp_preventivo_spese = comp_regroup_s[self.totale_label]

                context['w2_variation'] = self.calculate_variation(
                                        main_val=main_consuntivo_entrate['valore'],
                                        comp_val=comp_preventivo_entrate['valore'],
                                        )

                context['w3_variation'] = self.calculate_variation(
                                        main_val=main_consuntivo_spese['valore'],
                                        comp_val=comp_preventivo_spese['valore']
                                    )


        context["w1_showhelp"] = context["w2_showhelp"] = context["w3_showhelp"] = context["w4_showhelp"] = context["w5_showhelp"] = context["w6_showhelp"] = self.show_help
        context["w4_e_moneyverb"], context["w4_s_moneyverb"] = self.get_money_verb()
        context["w6_main_bilancio_type_plural"]= self.main_bilancio_type[:-1]+"i"


        return context


    def get_context_data(self, **kwargs):

        widget1 = widget2 = widget3 = None
        main_regroup_e = main_regroup_s=variations_e=variations_s= None

        context = super(BilancioCompositionWidgetView, self).get_context_data( **kwargs)

        ##
        # creates the context to feed the Visup composition widget
        ##

        context['year'] = self.main_bilancio_year

        if self.widget_type == "overview":

            context.update(self.create_context_overview())


        elif self.widget_type == "entrate":
            context.update(self.create_context_entrate())

        else:
            context.update(self.create_context_spese())


        context['comp_bilancio_type'] = self.comp_bilancio_type
        context['comp_bilancio_year'] = self.comp_bilancio_year


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

        if incarichi_set_1:
            incarichi_set_1.extend(incarichi_set_2)
            incarichi = incarichi_set_1
        else:
            incarichi = incarichi_set_2

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
                    "timeSpans":incarichi,
                    'data':data,
                    'legend':{'title':None,'items':legend}
                }
            ),
            content_type="application/json"
        )
    


class BilancioRedirectView(RedirectView):

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


class BilancioView(DetailView):

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


class BilancioNotFoundView(TemplateView):

    ##
    # show a page when a Comune doesnt have any bilancio
    ##

    template_name = "bilanci/bilancio_not_found.html"



class BilancioOverView(ShareUrlMixin, CalculateVariationsMixin, BilancioView):
    template_name = 'bilanci/bilancio_overview.html'
    selected_section = "bilancio"
    year = None
    main_bilancio_year = comp_bilancio_year = None
    main_bilancio_type = comp_bilancio_type = None
    comparison_not_available = False
    main_gdp_deflator = comp_gdb_deflator = None
    main_gdp_multiplier = comp_gdp_multiplier = 1.0
    territorio = None
    values_type = None
    cas_com_type = None
    fun_int_view = None
    share_url = None


    def calc_variations_set(self, main_dict, comp_dict,):
        # creates a variations list of dict based on voce denominazione
        variations = []
        for main_denominazione, main_value_dict in main_dict.iteritems():

            main_value = main_value_dict['valore']

            #  gets comparison value for the same voce
            # checks also for voce with denominazione followed by space: bug

            main_denominazione_strip = main_denominazione.strip()
            comparison_value_dict = comp_dict.get(main_denominazione_strip,{})
            if comparison_value_dict == {}:
                comparison_value_dict = comp_dict.get(main_denominazione_strip+" ",{})


            comparison_value = comparison_value_dict.get('valore',None)

            variation_dict = {
                'slug': main_value_dict['voce__slug'],
                'denominazione' :main_denominazione_strip,
                'variation': self.calculate_variation(
                                main_value,
                                comparison_value
                       )
                    }

            variations.append(variation_dict )

        return variations

    # return data_regroup for bilancio for selected year
    def get_data(self, slugset, year):

        values = ValoreBilancio.objects.filter(
            voce__slug__in=slugset,
            anno = year,
            territorio=self.territorio
        ).values('voce__denominazione', 'voce__level', 'anno','valore','valore_procapite','voce__slug').order_by('voce__denominazione','anno')

        keygen = lambda x: x['voce__denominazione']
        values_regroup = dict((k,list(v)[0]) for k,v in groupby(values, key=keygen))

        return values_regroup

    def get_chi_guardagna_perde(self, value_set, ):
        results=[]
        values_not_null=[]
        n_total_elements = 4
        n_half_elements = n_total_elements/2
        n_negs=0
        n_pos=0
        negs_to_add=2
        pos_to_add=2

        for value in value_set:
            if value['variation'] is not None:
                if value['variation'] < 0:
                    n_negs+=1
                elif value['variation'] > 0:
                    n_pos +=1

                values_not_null.append(value)


        # sets how many pos or neg values are needed to have a grand total
        # of 4 elements in the result list
        if n_negs < 2 or n_pos < 2:

            if n_negs < n_half_elements and n_pos < n_half_elements:

                if n_negs == 0 and n_pos == 0:
                    return results

                pos_to_add = n_pos
                negs_to_add = n_negs

            else:
                if n_negs < n_half_elements:
                    negs_to_add = n_negs
                    pos_to_add = n_total_elements-n_negs
                else:
                    pos_to_add = n_pos
                    negs_to_add = n_total_elements-n_pos

        pos_values = values_not_null[-pos_to_add:]
        neg_values = values_not_null[:negs_to_add]

        results.extend(pos_values[::-1])
        results.extend(neg_values[::-1])

        # if results < n_total elements, fills in with none values
        if len(results) < n_total_elements:
            diff = n_total_elements-len(results)
            results.extend(repeat(None,diff))

        return results


    def get(self, request, *args, **kwargs):

        ##
        # if year or type parameter are missing redirects to a page for default year / default bilancio type
        ##

        must_redirect = False
        self.territorio = self.get_object()
        self.year = self.request.GET.get('year', settings.SELECTOR_DEFAULT_YEAR)
        self.main_bilancio_type = self.request.GET.get('type', settings.SELECTOR_DEFAULT_BILANCIO_TYPE)

        self.values_type = self.request.GET.get('values_type', 'real')
        self.cas_com_type = self.request.GET.get('cas_com_type', 'cassa')

        if self.main_bilancio_type == "preventivo":
            self.cas_com_type = "cassa"


        # identifies the bilancio for comparison, sets gdp multiplier based on deflator

        self.main_bilancio_year = int(self.year)
        if self.main_bilancio_type == 'preventivo':
            self.comp_bilancio_type = 'consuntivo'
            verification_voice = self.comp_bilancio_type+'-entrate'
            self.comp_bilancio_year = self.territorio.best_year_voce(year=self.main_bilancio_year-1, slug = verification_voice )

        else:
            self.comp_bilancio_type = 'preventivo'
            verification_voice = self.comp_bilancio_type+'-entrate'
            self.comp_bilancio_year = self.territorio.best_year_voce(year=self.main_bilancio_year, slug = verification_voice )

        if self.comp_bilancio_year is None:
            self.comparison_not_available = True


        # sets current gdp deflator
        self.main_gdp_deflator = settings.GDP_DEFLATORS[int(self.main_bilancio_year)]

        if not self.comparison_not_available:
            self.comp_gdb_deflator = settings.GDP_DEFLATORS[int(self.comp_bilancio_year)]

        if self.values_type == 'real':
            self.main_gdp_multiplier = self.main_gdp_deflator
            if not self.comparison_not_available:
                self.comp_gdp_multiplier = self.comp_gdb_deflator

        if self.comp_bilancio_year is None:
            self.comparison_not_available = True


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

        rootnode_slug = rootnode_slugs[self.main_bilancio_type]['entrate'][self.cas_com_type]
        if self.selected_section != 'bilancio':
            rootnode_slug = rootnode_slugs[self.main_bilancio_type][self.selected_section][self.cas_com_type]

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
                        self.main_bilancio_type,
                        self.values_type,
                        self.cas_com_type
                    )
            )

        return super(BilancioOverView, self).get(request, *args, **kwargs)


    def get_context_data(self, **kwargs ):

        context = super(BilancioOverView, self).get_context_data(**kwargs)
        
        query_string = self.request.META['QUERY_STRING']

        context['tipo_bilancio'] = self.main_bilancio_type
        context['selected_bilancio_type'] = self.main_bilancio_type

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

        # chi guadagna / perde

        # entrate data
        main_ss_e , main_tot_e = self.get_slugset_entrate(self.main_bilancio_type,self.cas_com_type,include_totale=False)
        comp_ss_e, comp_tot_e = self.get_slugset_entrate(self.comp_bilancio_type, self.cas_com_type,include_totale=False)
        main_regroup_e = self.get_data(main_ss_e, self.main_bilancio_year)
        comp_regroup_e = self.get_data(comp_ss_e, self.comp_bilancio_year)
        variations_e = self.calc_variations_set(main_regroup_e, comp_regroup_e,)
        variations_e_sorted = sorted(variations_e, key=itemgetter('variation'))
        context['entrate_chiguadagnaperde'] = self.get_chi_guardagna_perde(variations_e_sorted)

        # spese data
        main_ss_s, main_tot_s = self.get_slugset_spese(self.main_bilancio_type, self.cas_com_type, include_totale=False)
        comp_ss_s, comp_tot_s = self.get_slugset_spese(self.comp_bilancio_type, self.cas_com_type, include_totale=False)
        main_regroup_s = self.get_data(main_ss_s, self.main_bilancio_year)
        comp_regroup_s = self.get_data(comp_ss_s, self.comp_bilancio_year)
        variations_s = self.calc_variations_set(main_regroup_s, comp_regroup_s,)
        variations_s_sorted = sorted(variations_s, key=itemgetter('variation'))
        context['spese_chiguadagnaperde'] = self.get_chi_guardagna_perde(variations_s_sorted)

        context['comparison_bilancio_type']=self.comp_bilancio_type
        context['comparison_bilancio_year']=self.comp_bilancio_year
        context['share_url']=self.share_url

        context['menu_voices'] = OrderedDict([
            ('bilancio', reverse('bilanci-overview', kwargs=menu_voices_kwargs)),
            ('entrate', reverse('bilanci-entrate', kwargs=menu_voices_kwargs)),
            ('spese', reverse('bilanci-spese', kwargs=menu_voices_kwargs)),
            ('indicatori', reverse('bilanci-indicatori', kwargs=menu_voices_kwargs))
        ])

        return context

class BilancioIndicatoriView(ShareUrlMixin, DetailView, IndicatorSlugVerifierMixin):
    model = Territorio
    context_object_name = "territorio"
    template_name = 'bilanci/bilancio_indicatori.html'
    selected_section = "indicatori"
    share_url = None
    territorio = None
    
    def get(self, request, *args, **kwargs):

        ##
        # if parameter is missing redirects to a page for default indicator
        ##
        self.territorio = self.get_object()

        if self.request.GET.get('slug') is None:
            return HttpResponseRedirect(reverse('bilanci-indicatori', kwargs={'slug':self.territorio.slug})\
                                        + "?slug={0}".format(settings.DEFAULT_INDICATOR_SLUG))

        return super(BilancioIndicatoriView, self).get(request, *args, **kwargs)



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

        context['indicator_list'] = Indicatore.objects.filter(published=True).order_by('denominazione')

        # creates the query string to call the IncarichiIndicatori Json view in template
        context['selected_indicators'] = selected_indicators_slugs
        context['selected_indicators_qstring'] = '?slug='+'&slug='.join(selected_indicators_slugs)
        context['share_url']=self.share_url
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
        context['bilancio_type'] = self.main_bilancio_type

        if self.main_bilancio_type == 'preventivo':
            context['bilancio_type_title'] = 'preventivi'
        else:
            context['bilancio_type_title'] = 'consuntivi'

        # chi guadagna / perde
        if self.selected_section == 'entrate':
            # entrate data
            main_ss_e , main_tot_e = self.get_slugset_entrate(self.main_bilancio_type,self.cas_com_type,include_totale=False)
            comp_ss_e, comp_tot_e = self.get_slugset_entrate(self.comp_bilancio_type, self.cas_com_type,include_totale=False)
            main_regroup_e = self.get_data(main_ss_e, self.main_bilancio_year)
            comp_regroup_e = self.get_data(comp_ss_e, self.comp_bilancio_year)
            variations_e = self.calc_variations_set(main_regroup_e, comp_regroup_e,)
            variations_e_sorted = sorted(variations_e, key=itemgetter('variation'))
            context['chiguadagnaperde'] = self.get_chi_guardagna_perde(variations_e_sorted)
        else:
            # spese data
            main_ss_s, main_tot_s = self.get_slugset_spese(self.main_bilancio_type, self.cas_com_type, include_totale=False)
            comp_ss_s, comp_tot_s = self.get_slugset_spese(self.comp_bilancio_type, self.cas_com_type, include_totale=False)
            main_regroup_s = self.get_data(main_ss_s, self.main_bilancio_year)
            comp_regroup_s = self.get_data(comp_ss_s, self.comp_bilancio_year)
            variations_s = self.calc_variations_set(main_regroup_s, comp_regroup_s,)
            variations_s_sorted = sorted(variations_s, key=itemgetter('variation'))
            context['chiguadagnaperde'] = self.get_chi_guardagna_perde(variations_s_sorted)

        return context


class BilancioEntrateView(BilancioDetailView):
    template_name = 'bilanci/bilancio_entrate.html'
    selected_section = "entrate"

    def get_slug(self):
        cassa_competenza_type = self.cas_com_type
        if self.cas_com_type == 'competenza':
            cassa_competenza_type = 'accertamenti'

        if self.main_bilancio_type == 'preventivo':
            return "{0}-{1}".format(self.main_bilancio_type,"entrate")
        else:
            return "{0}-{1}".format(
                self.main_bilancio_type,
                "entrate-{0}".format(cassa_competenza_type)
            )



class BilancioSpeseView(BilancioDetailView):
    template_name = 'bilanci/bilancio_spese.html'
    selected_section = "spese"

    def get_slug(self):
        cassa_competenza_type = self.cas_com_type
        if self.cas_com_type == 'competenza':
            cassa_competenza_type = 'impegni'

        if self.main_bilancio_type == 'preventivo':
            return "{0}-{1}".format(self.main_bilancio_type,"spese")
        else:
            return "{0}-{1}".format(
                self.main_bilancio_type,
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


class ClassificheRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        # redirects to Classifiche starting page when coming from navbar
        kwargs['parameter_type'] = 'entrate'
        kwargs['parameter_slug'] = settings.DEFAULT_VOCE_SLUG_CLASSIFICHE
        kwargs['anno'] = settings.CLASSIFICHE_END_YEAR

        try:
            url = reverse('classifiche-list', args=args , kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url


class ClassificheSearchView(RedirectView):

    paginate_by = settings.CLASSIFICHE_PAGINATE_BY

    def get(self, request, *args, **kwargs):
        ##
        # catches the user search for a territorio,
        # redirects to the correct classifiche list page highlighting the chosen territorio
        ##

        territorio_found = True
        selected_cluster = request.GET.get('selected_cluster').split(',')
        selected_regioni = request.GET.get('selected_regioni').split(',')
        selected_par_type = request.GET.get('selected_par_type')
        selected_parameter_id = request.GET.get('selected_parameter_id')
        territorio_id = int(request.GET.get('territorio_id'))
        selected_year = request.GET.get('selected_year')

        selected_regioni_names = Territorio.objects.filter(pk__in=selected_regioni).values_list('denominazione',flat=True)
        territori_baseset = list(Territorio.objects.filter(cluster__in=selected_cluster, regione__in=selected_regioni_names).values_list('pk',flat=True))

        if selected_par_type == 'indicatori':
            all_ids = ValoreIndicatore.objects.get_classifica_ids(selected_parameter_id, selected_year)
            parameter_slug = Indicatore.objects.get(pk=selected_parameter_id).slug
        else:
            all_ids = ValoreBilancio.objects.get_classifica_ids(selected_parameter_id, selected_year)
            parameter_slug = Voce.objects.get(pk=selected_parameter_id).slug

        try:
            territorio_idx =  [id for id in all_ids if id in territori_baseset].index(territorio_id)
            territorio_page = (territorio_idx / self.paginate_by)+1
        except ValueError:
            territorio_page = 1
            territorio_found = False

        kwargs['parameter_type'] = selected_par_type
        kwargs['parameter_slug'] = parameter_slug
        kwargs['anno'] = selected_year

        try:
            url = reverse('classifiche-list', args=args , kwargs=kwargs)+\
                  '?' +"r="+"&r=".join(selected_regioni)+"&c="+"&c=".join(selected_cluster)+'&page='+str(territorio_page)

            if territorio_found:
                url +='&hl='+str(territorio_id)
        except NoReverseMatch:
            url = reverse('404')



        return HttpResponseRedirect(url)

    def get_redirect_url(self, *args, **kwargs):
        if True:
            pass
        pass



class ClassificheListView(ListView):

    template_name = 'bilanci/classifiche.html'
    paginate_by = settings.CLASSIFICHE_PAGINATE_BY
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

        selected_regioni_get = [int(k) for k in self.request.GET.getlist('r')]
        if len(selected_regioni_get):
            self.selected_regioni = selected_regioni_get

        selected_cluster_get = self.request.GET.getlist('c')
        if len(selected_cluster_get):
            self.selected_cluster = selected_cluster_get

        return super(ClassificheListView, self).get(self, request, *args, **kwargs)

    def get_queryset(self):
        # read current and previous years' lit of Territorio ids, sorted by descending procapite
        #in order to create the paginated Classifica page, with the delta on positions from previous year
        self.curr_year = self.anno_int
        self.prev_year = self.anno_int - 1

        if self.parameter_type == 'indicatori':
            self.curr_ids = ValoreIndicatore.objects.get_classifica_ids(self.parameter.id, self.curr_year)
            self.prev_ids = ValoreIndicatore.objects.get_classifica_ids(self.parameter.id, self.prev_year)
        else:
            self.curr_ids = ValoreBilancio.objects.get_classifica_ids(self.parameter.id, self.curr_year)
            self.prev_ids = ValoreBilancio.objects.get_classifica_ids(self.parameter.id, self.prev_year)

        ##
        # Filters on regioni / cluster
        ##

        # initial territori_baseset is the complete list of comuni
        territori_baseset = Territorio.objects.comuni

        if len(self.selected_regioni):
            # this passege is necessary because in the regione field of territorio there is the name of the region
            selected_regioni_names = list(
                Territorio.objects.regioni.filter(pk__in=self.selected_regioni).values_list('denominazione',flat=True)
            )
            territori_baseset = territori_baseset.filter(regione__in=selected_regioni_names)

        if len(self.selected_cluster):
            territori_baseset = territori_baseset.filter(cluster__in=self.selected_cluster)

        territori_ids = list(territori_baseset.values_list('id', flat=True))

        self.curr_ids =  [id for id in self.curr_ids if id in territori_ids]
        self.prev_ids =  [id for id in self.prev_ids if id in territori_ids]

        self.queryset = self.curr_ids
        return self.queryset

    def get_context_data(self, **kwargs):

        # enrich the Queryset in object_list with Political context data and variation value
        object_list = []
        page = int(self.request.GET.get('page',1))

        paginator_offset = ((page - 1) * self.paginate_by) + 1

        all_regions = Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).values_list('pk',flat=True)
        all_clusters = Territorio.objects.filter(territorio=Territorio.TERRITORIO.L).values_list('cluster',flat=True)

        context = super(ClassificheListView, self).get_context_data( **kwargs)

        # creates context data based on the paginated queryset
        paginated_queryset = context['object_list']

        # regroups incarichi politici based on territorio
        incarichi_set = Incarico.get_incarichi_attivi_set(paginated_queryset, self.curr_year).select_related('territorio')
        incarichi_territorio_keygen = lambda x: x.territorio.pk
        incarichi_regroup = dict((k,list(v)) for k,v in groupby(incarichi_set, key=incarichi_territorio_keygen))

        # re-hydrate only objects in page
        filters = {
            'anno': self.curr_year,
            "territorio__id__in": paginated_queryset,
        }
        if self.parameter_type == 'indicatori':
            filters['indicatore__id'] = self.parameter.id
            objects = list(ValoreIndicatore.objects.filter(**filters).select_related())
        else:
            filters['voce__id'] = self.parameter.id
            objects = list(ValoreBilancio.objects.filter(**filters).select_related())
        objects_dict = dict((obj.territorio_id, obj) for obj in objects)

        # build context for objects in page, there are no db-access at this point
        for ordinal_position, territorio_id in enumerate(paginated_queryset, start=paginator_offset):
            incarichi = []

            obj = objects_dict[territorio_id]

            if self.parameter_type =='indicatori':
                valore = obj.valore

            else:
                valore = obj.valore_procapite

            if territorio_id in incarichi_regroup.keys():
                incarichi = incarichi_regroup[territorio_id]

            territorio_dict = {
                'territorio':{
                    'denominazione': obj.territorio.denominazione,
                    'slug': obj.territorio.slug,
                    'prov': obj.territorio.prov,
                    'regione': obj.territorio.regione,
                    'pk': obj.territorio.pk,
                    },
                'valore': valore,
                'variazione': 0,
                'incarichi_attivi': incarichi,
                'position': ordinal_position,
                'prev_position': ordinal_position,
            }

            # adjust prev position and variation if values are found
            if territorio_id in self.prev_ids:
                territorio_dict['variazione'] = self.prev_ids.index(territorio_id) - self.curr_ids.index(territorio_id)
                territorio_dict['prev_position'] = self.prev_ids.index(territorio_id) + 1


            object_list.append( territorio_dict )


        # updates obj list
        context['object_list'] = object_list
        context['n_comuni'] = len(self.queryset)

        # defines the lists of possible confrontation parameters
        context['selected_par_type'] = self.parameter_type
        context['selected_parameter'] = self.parameter
        context['selected_parameter_name'] = self.parameter.denominazione

        if self.parameter != 'indicatori':
            if self.parameter.slug == 'consuntivo-entrate-cassa':
                context['selected_parameter_name'] = 'Totale entrate'
            if self.parameter.slug == 'consuntivo-spese-cassa':
                context['selected_parameter_name'] = 'Totale spese'

        self.selected_regioni = list(self.selected_regioni) if len(self.selected_regioni)>0 else list(all_regions)
        self.selected_cluster = list(self.selected_cluster) if len(self.selected_cluster)>0 else list(all_clusters)

        context['selected_regioni'] = self.selected_regioni
        context['selected_cluster'] = self.selected_cluster
        selected_regioni_str = [str(k) for k in self.selected_regioni]
        selected_cluster_str = [str(k) for k in self.selected_cluster]

        # string version of form flags needed for classifiche search
        context['selected_regioni_str'] = ','.join(selected_regioni_str)
        context['selected_cluster_str'] = ','.join(selected_cluster_str)

        context['selected_year'] = self.anno
        context['selector_default_year'] = settings.CLASSIFICHE_END_YEAR
        context['selector_start_year'] = settings.CLASSIFICHE_START_YEAR
        context['selector_end_year'] = settings.CLASSIFICHE_END_YEAR

        entrate_list = list(Voce.objects.get(slug='consuntivo-entrate-cassa').get_children().order_by('slug').values('denominazione','slug'))
        entrate_list.append({'slug':'consuntivo-entrate-cassa','denominazione': u'Totale entrate'})

        spese_list = list(Voce.objects.get(slug=settings.CONSUNTIVO_SOMMA_SPESE_FUNZIONI_SLUG).get_children().order_by('slug').values('denominazione','slug'))
        spese_list.append({'slug': 'consuntivo-spese-cassa', 'denominazione': u'Totale spese'})

        context['indicator_list'] = Indicatore.objects.filter(published = True).order_by('denominazione')
        context['entrate_list'] = entrate_list
        context['spese_list'] = spese_list

        context['regioni_list'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).order_by('denominazione')
        context['cluster_list'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.L).order_by('-cluster')
        context['territori_search_form_classifiche'] = TerritoriSearchFormClassifiche()
        context['query_string'] = "r="+"&r=".join(selected_regioni_str)+"&c="+"&c=".join(selected_cluster_str)

        # if there is a territorio to highlight passes the data to context
        context['highlight_territorio'] = None
        territorio_highlight = self.request.GET.get('hl',None)

        if territorio_highlight is not None:
            context['highlight_territorio'] = int(territorio_highlight)

        # creates url for share button
        regioni_list=['',]
        regioni_list.extend([str(r) for r in self.selected_regioni])
        cluster_list=['',]
        cluster_list.extend(self.selected_cluster)

        # gets current page url
        long_url = self.request.build_absolute_uri(
            reverse('classifiche-list', kwargs={'anno':self.anno,'parameter_type':self.parameter_type, 'parameter_slug':self.parameter.slug})
            )+'?' + "&r=".join(regioni_list)+"&c=".join(cluster_list)+'&page='+str(context['page_obj'].number)
        # checks if short url is already in the db, otherwise asks to google to shorten the url

        short_url_obj=None
        try:
            short_url_obj = ShortUrl.objects.get(long_url = long_url)

        except ObjectDoesNotExist:

            payload = { 'longUrl': long_url+'&key='+settings.GOOGLE_SHORTENER_API_KEY }
            headers = { 'content-type': 'application/json' }
            try:
                short_url_req = requests.post(settings.GOOGLE_SHORTENER_URL, data=json.dumps(payload), headers=headers)
                if short_url_req.status_code == requests.codes.ok:
                    short_url = short_url_req.json().get('id')
                    short_url_obj = ShortUrl()
                    short_url_obj.short_url = short_url
                    short_url_obj.long_url = long_url
                    short_url_obj.save()
            except (ConnectionError, Timeout, SSLError, ProxyError):
                pass


        if short_url_obj:
            context['share_url'] = short_url_obj.short_url

        return context


class MappeTemplateView(TemplateView):

    ##
    # Shows simple map page
    ##

    template_name = "bilanci/mappe.html"

    def get_context_data(self, **kwargs):


        context = super(MappeTemplateView, self).get_context_data(**kwargs)


        return context



class ConfrontiHomeView(TemplateView):

    ##
    # ConfrontiHomeView shows the search form to compare two Territori
    ##

    template_name = "bilanci/confronti_home.html"

    def get_context_data(self, **kwargs):

        # generates the list of bilancio Voce and Indicators
        # for the selection menu displayed on page

        context = {'territori_comparison_search_form': TerritoriComparisonSearchForm(),}


        return context


class ConfrontiRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):

        # redirects to appropriate confronti view based on default parameter for Territori
        kwargs['parameter_slug'] = settings.DEFAULT_VOCE_SLUG_CONFRONTI

        try:
            url = reverse('confronti-entrate', args=args , kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url


class ConfrontiView(ShareUrlMixin, TemplateView):

    template_name = "bilanci/confronti_data.html"
    share_url = None
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

        return super(ConfrontiView,self).get(request,*args,**kwargs)



    def get_context_data(self, **kwargs):

        # construct common context data for Confronti View
        context = super(ConfrontiView, self).get_context_data( **kwargs)

        context['territorio_1'] = self.territorio_1
        context['territorio_2'] = self.territorio_2

        context['contesto_1'] = self.territorio_1.latest_contesto
        context['contesto_2'] = self.territorio_2.latest_contesto

        # defines the lists of possible confrontation parameters

        entrate_list = list(Voce.objects.get(slug='consuntivo-entrate-cassa').get_children().order_by('slug').values('denominazione','slug'))
        entrate_list.append({'slug':'consuntivo-entrate-cassa','denominazione': u'Totale entrate'})

        spese_list = list(Voce.objects.get(slug=settings.CONSUNTIVO_SOMMA_SPESE_FUNZIONI_SLUG).get_children().order_by('slug').values('denominazione','slug'))
        spese_list.append({'slug': 'consuntivo-spese-cassa', 'denominazione': u'Totale spese'})

        context['indicator_list'] = Indicatore.objects.filter(published = True).order_by('denominazione')
        context['entrate_list'] = entrate_list
        context['spese_list'] = spese_list
        context['share_url'] = self.share_url
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
        parameter = get_object_or_404(Voce, slug = kwargs['parameter_slug'])
        context['parameter'] = parameter

        context['parameter_name'] = parameter.denominazione
        if parameter.slug == 'consuntivo-entrate-cassa':
            context['parameter_name'] = u'Totale entrate'

        return context

class ConfrontiSpeseView(ConfrontiView):

    def get_context_data(self, **kwargs):
        context = super(ConfrontiSpeseView, self).get_context_data( **kwargs)
        context['parameter_type'] = "spese"
        parameter = get_object_or_404(Voce, slug = kwargs['parameter_slug'])
        context['parameter'] = parameter

        context['parameter_name'] = parameter.denominazione
        if parameter.slug == 'consuntivo-spese-cassa':
            context['parameter_name'] = u'Totale spese'


        return context

class ConfrontiIndicatoriView(ConfrontiView):

    def get_context_data(self, **kwargs):
        context = super(ConfrontiIndicatoriView, self).get_context_data( **kwargs)
        context['parameter_type'] = "indicatori"
        parameter = get_object_or_404(Indicatore, slug = kwargs['parameter_slug'])
        context['parameter'] = parameter
        context['parameter_name'] = parameter.denominazione

        return context


