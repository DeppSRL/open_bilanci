import logging
import os
import re
import zmq
import json
import requests
import feedparser
from operator import itemgetter
from itertools import groupby, ifilter, repeat
from collections import OrderedDict
from requests.exceptions import ConnectionError, Timeout, SSLError, ProxyError
from datetime import datetime, timedelta
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView, View, ListView
from django.conf import settings
from services.models import PaginaComune
from bilanci.forms import TerritoriComparisonSearchForm, EarlyBirdForm, TerritoriSearchFormHome, \
    TerritoriSearchFormClassifiche
from bilanci.models import ValoreBilancio, Voce, Indicatore, ValoreIndicatore, ImportXmlBilancio
import services
from shorturls.models import ShortUrl
from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, Http404
from territori.models import Territorio, Incarico


logger = logging.getLogger('bilanci_project')


class ServiziComuniMixin(object):
    territorio = None
    servizi_comuni = False

    def check_servizi_comuni(self, request):
        # identifies if the request comes from a Comuni host
        if request.servizi_comuni:
            self.servizi_comuni = True

    def get_servizi_comune_context(self):

        # gets PaginaComune data to pass onto the context
        try:
            p_comune = PaginaComune.objects.get(territorio=self.territorio, active=True)
        except ObjectDoesNotExist:
            return None
        else:
            return p_comune


class ShareUrlMixin(object):
    share_url = None

    def get(self, request, *args, **kwargs):

        # gets current page url
        long_url = "http://" + request.META['HTTP_HOST'] + request.get_full_path()

        if len(long_url) < 80:
            self.share_url = long_url

        else:
            # checks if short url is already in the db, otherwise asks to google to shorten the url

            short_url_obj = None
            try:
                short_url_obj = ShortUrl.objects.get(long_url=long_url)

            except ObjectDoesNotExist:

                payload = {'longUrl': long_url + '&key=' + settings.GOOGLE_SHORTENER_API_KEY}
                headers = {'content-type': 'application/json'}
                try:
                    short_url_req = requests.post(settings.GOOGLE_SHORTENER_URL, data=json.dumps(payload), headers=headers)
                except (ConnectionError, Timeout, SSLError, ProxyError):
                    logger.warning("Error connecting with Google url shortener service")
                else:
                    if short_url_req.status_code == requests.codes.ok:
                        short_url = short_url_req.json().get('id')
                        short_url_obj = ShortUrl()
                        short_url_obj.short_url = short_url
                        short_url_obj.long_url = long_url
                        short_url_obj.save()

            if short_url_obj:
                self.share_url = short_url_obj.short_url

        return super(ShareUrlMixin, self).get(request, *args, **kwargs)


class NavigationMenuMixin(object):
    entrate_kwargs = {'section': 'entrate'}
    spese_kwargs = {'section': 'spese'}

    def get_menu_voices(self, ):

        # generates menu_voices structure based on if the request comes from Servizi comune or main app

        urlconf = None
        destination_views = {
            'overview': 'bilanci-overview',
            'dettaglio': 'bilanci-dettaglio',
            'composizione': 'bilanci-composizione',
            'indicatori': 'bilanci-indicatori',
        }

        kwargs = {
            'overview': {'slug': self.territorio.slug},
            'indicatori': {'slug': self.territorio.slug},
        }

        if hasattr(self, 'entrate_kwargs'):
            kwargs['entrate'] = self.entrate_kwargs

        if hasattr(self, 'spese_kwargs'):
            kwargs['spese'] = self.spese_kwargs

        # if the request comes from Comune host then changes the url in the nav menu
        # basically resolving the path with services.urls and popping the territorio slug from kwargs
        if self.servizi_comuni:
            urlconf = services.urls
            destination_views = {
                'overview': 'bilanci-overview-services',
                'dettaglio': 'bilanci-dettaglio-services',
                'composizione': 'bilanci-composizione-services',
                'indicatori': 'bilanci-indicatori-services',
            }
            kwargs['indicatori'] = None
            kwargs['overview'] = None
            if 'entrate' in kwargs.keys():
                kwargs['entrate'].pop("slug", None)
            if 'spese' in kwargs.keys():
                kwargs['spese'].pop("slug", None)

        menu_voices = OrderedDict([
            ('bilancio', reverse(destination_views['overview'], kwargs=kwargs['overview'], urlconf=urlconf)),
            ('entrate', OrderedDict([
                ('dettaglio',
                 reverse(destination_views['dettaglio'], kwargs=kwargs.get('entrate', None), urlconf=urlconf)),
                ('composizione',
                 reverse(destination_views['composizione'], kwargs=kwargs.get('entrate', None), urlconf=urlconf))
            ])),
            ('spese', OrderedDict([
                ('dettaglio',
                 reverse(destination_views['dettaglio'], kwargs=kwargs.get('spese', None), urlconf=urlconf)),
                ('composizione',
                 reverse(destination_views['composizione'], kwargs=kwargs.get('spese', None), urlconf=urlconf)),
            ])),
            ('indicatori', reverse(destination_views['indicatori'], kwargs=kwargs['indicatori'], urlconf=urlconf))
        ])

        return menu_voices


class MiniClassificheMixin(object):

    def get_positions(self, element_list, territori_ids):

        # calculates positions for values considering that if two (or more) territorio
        # have the same value for indicatore / voce their position will be the same

        positions = {}

        # filter the whole list based on which territori are the baseset for this classifica
        filtered_list = [element for element in element_list if element['territorio__id'] in territori_ids]

        for idx, element in enumerate(filtered_list):
            territorio_id = element['territorio__id']
            if idx == 0:
                positions[territorio_id] = 1
            else:
                previous_id = filtered_list[idx - 1]['territorio__id']
                previous_value = filtered_list[idx - 1]['valore']

                if round(element['valore'], 2) == round(previous_value, 2):
                    positions[territorio_id] = positions[previous_id]
                else:
                    positions[territorio_id] = positions[previous_id] + 1

        return positions

    def get_indicatore_positions(self, territorio, anno):
        # construct data for mini classifiche
        indicatori = Indicatore.objects.filter(published=True).values('pk', 'denominazione', 'slug')

        # initial territori_baseset is the complete list of comuni in the same cluster as territorio
        territori_cluster = Territorio.objects.comuni.filter(cluster=territorio.cluster)
        territori_cluster_id = list(territori_cluster.values_list('id', flat=True))

        indicatore_position = []

        for indicatore in indicatori:

            indicatore_all_ids = ValoreIndicatore.objects.get_classifica_ids(indicatore['pk'], anno)
            # filters results on territori in the considered cluster
            position = self.get_positions(indicatore_all_ids, territori_cluster_id)

            if territorio.pk in position:
                indicatore_position.append(
                    {
                        'indicatore_denominazione': indicatore['denominazione'],
                        'indicatore_pk': indicatore['pk'],
                        'indicatore_slug': indicatore['slug'],
                        'position': position[territorio.pk]
                    }
                )

        return indicatore_position


class HierarchicalMenuMixin(object):
    def get_parameter_struct(self):
        # defines the parameter list shown in the hierarchical menu and avoids showing descendants of Prestiti for Entrate/Spese
        entrate_prestiti_descendants = Voce.objects.get(slug='consuntivo-entrate-cassa-prestiti').get_descendants(
            include_self=False).values_list('slug', flat=True)
        entrate_set = Voce.objects.get(slug='consuntivo-entrate-cassa').get_descendants(include_self=True).exclude(
            slug__in=entrate_prestiti_descendants).order_by('denominazione')
        entrate_list = [entrate_set, ]

        # spese_funzioni_list = list(Voce.objects.get(slug=settings.CONSUNTIVO_SOMMA_SPESE_FUNZIONI_SLUG).get_descendants(include_self=True).order_by('denominazione'))
        spese_funzioni = Voce.objects.get(slug=settings.CONSUNTIVO_SOMMA_SPESE_FUNZIONI_SLUG).get_descendants(
            include_self=True).order_by('denominazione')

        # spese_prestiti = list(Voce.objects.filter(slug = 'consuntivo-spese-cassa-prestiti'))
        spese_prestiti = Voce.objects.filter(slug='consuntivo-spese-cassa-prestiti')

        spese_funzioni_list = [spese_funzioni, spese_prestiti]

        spese_interventi_investimenti = Voce.objects.get(
            slug=settings.CONSUNTIVO_SPESE_INVESTIMENTI_INTERVENTI_SLUG).get_descendants(include_self=True)
        spese_interventi_correnti = Voce.objects.get(
            slug=settings.CONSUNTIVO_SPESE_CORRENTI_INTERVENTI_SLUG).get_descendants(include_self=True)

        spese_interventi_list = [spese_interventi_correnti, spese_interventi_investimenti, spese_prestiti]

        indicator_list = [Indicatore.objects.filter(published=True).order_by('denominazione'), ]

        return {
            'indicatori': indicator_list,
            'entrate': entrate_list,
            'spese_funzioni': spese_funzioni_list,
            'spese_interventi': spese_interventi_list
        }

    @staticmethod
    def get_classifiche_parameters():
        # provide a dict of Voce slug of Voce that can appear in Classifiche,
        # used both in the Hierarchical menu and in Dettaglio page to check that Voce is allowed a Classifiche link

        hmm = HierarchicalMenuMixin()
        parameter_struct = hmm.get_parameter_struct()

        entrate = list(parameter_struct['entrate'][0].values_list('slug', flat=True))

        spese_funzioni_list = list(parameter_struct['spese_funzioni'][0])
        spese_funzioni_list.remove(Voce.objects.get(slug=u'consuntivo-spese-cassa-spese-somma-funzioni'))
        spese_funzioni_list.extend(list(parameter_struct['spese_funzioni'][1]))
        spese_funzioni = [x.slug for x in spese_funzioni_list]

        spese_interventi_list = list(parameter_struct['spese_interventi'][0])
        spese_interventi_list.extend(list(parameter_struct['spese_interventi'][1]))
        spese_interventi_list.extend(list(parameter_struct['spese_interventi'][2]))
        spese_interventi = [x.slug for x in spese_interventi_list]

        return {
            'entrate': entrate,
            'spese_funzioni': spese_funzioni,
            'spese_interventi': spese_interventi
        }


class StaticPageView(TemplateView, ServiziComuniMixin, NavigationMenuMixin):
    template_name = 'static_page.html'

    def get(self, request, *args, **kwargs):

        # check if the request comes from Comuni host
        self.check_servizi_comuni(request)
        if self.servizi_comuni:
            self.territorio = Territorio.objects.get(slug=kwargs['slug'])

        page_url = request.get_full_path().replace("/pages/", "")
        if page_url not in settings.ENABLED_STATIC_PAGES:
            if self.servizi_comuni:
                return HttpResponseRedirect(reverse('bilanci-overview-services', urlconf=services.urls))
            else:
                return HttpResponseRedirect(reverse('404'))
        return super(StaticPageView, self).get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(StaticPageView, self).get_context_data(**kwargs)

        # if servizi_comuni then passes the Pagina Comune data to the template
        if self.servizi_comuni:
            context['pagina_comune'] = self.get_servizi_comune_context()
            context['territorio'] = self.territorio
            context['menu_voices'] = self.get_menu_voices()
            self.template_name = 'services/static_page.html'

        return context


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['territori_search_form_home'] = TerritoriSearchFormHome()
        op_blog_posts = cache.get('blog-posts')
        if op_blog_posts is None:
            op_blog_posts = feedparser.parse(
                'http://blog.openpolis.it/categorie/%s/feed/' % settings.OP_BLOG_CATEGORY).entries[:3]
            for post in op_blog_posts:
                try:
                    post['excerpt'] = post.content[0].value.split('<span id="more-')[0]
                except:
                    pass
            cache.set('blog-posts', op_blog_posts, timeout=120)
        context['op_blog_posts'] = op_blog_posts
        context['import_xml'] = list(ImportXmlBilancio.objects.all().order_by('data_fornitura'))
        return context


class HomeTemporaryView(TemplateView):
    template_name = "home_temporary.html"

    def get_context_data(self, **kwargs):
        context = super(HomeTemporaryView, self).get_context_data(**kwargs)
        context['form'] = EarlyBirdForm()
        return context

    def post(self, request, *args, **kwargs):
        ##
        # Send form data to the mailbin queue
        ##

        context = self.get_context_data(**kwargs)

        context['form'] = form = EarlyBirdForm(self.request.POST)

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
            context['has_errors'] = True
        return self.render_to_response(context)


class IndicatorSlugVerifierMixin(object):
    ##
    # IndicatorSlugVerifier given a slug list of Indicatore verifies that all slug exist
    # returns a list of those slugs that were verified
    ##

    def verify_slug(self, slug_list):

        verified_slug_list = []
        # verify that all indicators exist and creates a verified list of slugs
        for ind_slug in slug_list:
            try:
                Indicatore.objects.get(slug=ind_slug)
            except ObjectDoesNotExist:
                pass
            else:
                verified_slug_list.append(ind_slug)

        return verified_slug_list


class IncarichiGetterMixin(object):
    date_fmt = '%Y-%m-%d'
    #     sets the start / end of graphs
    timeline_start_date = settings.APP_START_DATE.date()
    timeline_end_date = settings.APP_END_DATE.date()
    #  max n. of days between two incarichi. if difference > max then a disabled incarico is added
    max_incarichi_gap = 30
    empty_gap_days = 5

    def insert_disabled_incarico(self, data_1, data_2):
        diff_days = abs(data_1 - data_2).days

        if diff_days >= self.max_incarichi_gap:

            disabled_incarico = {
                'start': (data_1 + timedelta(days=self.empty_gap_days)).strftime(self.date_fmt),
                'end': (data_2 - timedelta(days=self.empty_gap_days)).strftime(self.date_fmt),
                'icon': None,
                'label': None,
                'sublabel': None
            }
            return disabled_incarico
        else:
            return None


    def transform_incarichi(self, incarichi_set, highlight_color):


        incarichi_transformed = []

        for incarico in incarichi_set:

            dict_widget = {
                # sets incarico marker color and highlight
                'icon': settings.INCARICO_MARKER_DUMMY,
                'color': settings.INCARICO_MARKER_INACTIVE,
                'highlightColor': highlight_color,
                'start': None,
                'end': None,
                }

            # exclude wrong cases
            if not incarico.data_inizio:
                continue

            # exclude cases out of the considered timeline interval
            if incarico.data_inizio > self.timeline_end_date or \
                (incarico.data_fine and incarico.data_fine < self.timeline_start_date):
                continue


            # truncates date start to timeline start
            if incarico.data_inizio < self.timeline_start_date:
                dict_widget['start'] = self.timeline_start_date.strftime(self.date_fmt)
            else:
                dict_widget['start'] = incarico.data_inizio.strftime(self.date_fmt)

            if not incarico.data_fine:
                dict_widget['end'] = self.timeline_end_date.strftime(self.date_fmt)
            else:
                if incarico.data_fine > self.timeline_end_date:
                    dict_widget['end'] = self.timeline_end_date.strftime(self.date_fmt)
                else:
                    dict_widget['end'] = incarico.data_fine.strftime(self.date_fmt)

            if incarico.pic_url:
                dict_widget['icon'] = incarico.pic_url

            if incarico.tipologia == Incarico.TIPOLOGIA.commissario:
                # commissari
                dict_widget['label'] = "Commissario".title()
                dict_widget['icon'] = settings.INCARICO_MARKER_COMMISSARIO
                if incarico.motivo_commissariamento:
                    dict_widget['sublabel'] = incarico.motivo_commissariamento.title()

            else:

                # sets sindaco / vicesindaco name, surname
                dict_widget['label'] = "{0}".format(incarico.cognome.title().encode('utf-8'), )

                if incarico.tipologia == Incarico.TIPOLOGIA.vicesindaco_ff:
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
                        dict_widget['sublabel'] = ''

            incarichi_transformed.append(dict_widget)

        disabled_list = []
        # if needed adds data for disabled incarichi
        for idx, incarico in enumerate(incarichi_transformed):
            if idx is 0:
                # check distante between first incarico and timeline start
                disabled_incarico = self.insert_disabled_incarico(self.timeline_start_date,
                                                                  datetime.strptime(incarico['start'],
                                                                                    self.date_fmt).date())
                if disabled_incarico:
                    disabled_list.append(disabled_incarico)

            elif idx == len(incarichi_transformed) - 1:
                # check distante between last incarico and timeline end
                disabled_incarico = self.insert_disabled_incarico(
                    datetime.strptime(incarico['end'], self.date_fmt).date(), self.timeline_end_date)
                if disabled_incarico:
                    disabled_list.append(disabled_incarico)

            else:
                #se la differenza tra l'incarico attuale e il precedente > max
                # inserisce un incarico vuoto per far comparire la bacchetta vuota nella timeline
                disabled_incarico = self.insert_disabled_incarico(
                    datetime.strptime(incarichi_transformed[idx - 1]['end'], self.date_fmt).date(),
                    datetime.strptime(incarico['start'], self.date_fmt).date())
                if disabled_incarico:
                    disabled_list.append(disabled_incarico)

        incarichi_transformed.extend(disabled_list)
        return incarichi_transformed


    def get_incarichi_struct(self, territorio_opid, highlight_color):

        incarichi_set = Incarico.objects.filter(territorio__op_id=territorio_opid).order_by('data_inizio')
        transformed_set = self.transform_incarichi(incarichi_set, highlight_color)

        if len(transformed_set):
            return [transformed_set]
        else:
            return []


    ##
    # transform bilancio values to be feeded to Visup widget
    ##

    def transform_for_widget(self, voce_values, line_id, line_color, decimals=0, per_capita=False):

        line_dict = {
            'id': line_id,
            'color': line_color,
            'series': []
        }

        serie = []

        for voce_value in voce_values:

            # considers absolute or per_capita values
            if per_capita is False:
                value_to_consider = voce_value.get('valore', None)
            else:
                value_to_consider = voce_value.get('valore_procapite', None)

            if value_to_consider is not None:
                valore = value_to_consider

                serie.append(
                    [voce_value['anno'], round(valore, decimals)]
                )
            else:
                serie.append(
                    [voce_value['anno'], None]
                )

        # before returning the data struct checks if there is any missing year in the data set:
        # if so adds a list of [missing_year, None] to the serie: this creates a gap in the line chart

        fill_in = False
        for idx, [year, valore] in enumerate(serie):
            if idx != 0:
                prev_yr = serie[idx - 1][0]
                yr_difference = year - prev_yr
                if yr_difference > 1:
                    fill_in_yr = prev_yr + 1
                    while fill_in_yr <= year - 1:
                        serie.append([fill_in_yr, None])
                        fill_in = True
                        fill_in_yr += 1


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

    def get_voce_struct(self, territorio, voce_bilancio, line_id, line_color, per_capita=False):

        voce_values = ValoreBilancio.objects.filter(
            territorio=territorio,
            voce=voce_bilancio,
            anno__gte=self.timeline_start_date.year,
            anno__lte=self.timeline_end_date.year
        ).values('anno', 'valore', 'valore_procapite').order_by('anno')

        return self.transform_for_widget(voce_values, line_id, line_color, per_capita=per_capita)

    ##
    # get indicatori values of specified Indicatore for Territorio in the time span
    ##

    def get_indicatore_struct(self, territorio, indicatore, line_id, line_color):

        indicatore_values = ValoreIndicatore.objects.filter(
            territorio=territorio,
            indicatore=indicatore,
            anno__gte=self.timeline_start_date.year,
            anno__lte=self.timeline_end_date.year
        ).values('anno', 'valore').order_by('anno')

        return self.transform_for_widget(indicatore_values, line_id, line_color, decimals=2)


class IncarichiVoceJSONView(View, IncarichiGetterMixin):
    def get(self, request, **kwargs):

        # get territorio_opid from GET parameter
        territorio_opid = kwargs['territorio_opid']
        territorio = get_object_or_404(Territorio, op_id=territorio_opid)

        # gets the Territorio that is the cluster to which the considered territorio belongs
        cluster = Territorio.objects.get(
            territorio=Territorio.TERRITORIO.L,
            cluster=territorio.cluster,
        )

        # get voce bilancio from GET parameter
        voce_slug = kwargs['voce_slug']
        if voce_slug:
            voce_bilancio = get_object_or_404(Voce, slug=voce_slug)
        else:
            return HttpResponseRedirect(reverse('404'))

        incarichi_set = self.get_incarichi_struct(territorio_opid, highlight_color=settings.TERRITORIO_1_COLOR)

        # gets voce value for the territorio over the period set
        # check nominal or real values in query string
        voce_set = self.get_voce_struct(
            territorio,
            voce_bilancio,
            line_id=1,
            line_color=settings.TERRITORIO_1_COLOR,
            per_capita=True
        )

        cluster_mean_set = self.get_voce_struct(
            cluster,
            voce_bilancio,
            line_id=2,
            line_color=settings.CLUSTER_LINE_COLOR,
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
            'title': None,

            "items": [
                {
                    "color": settings.TERRITORIO_1_COLOR,
                    "id": 1,
                    "label": voce_line_label.upper()
                },
                {
                    "color": settings.CLUSTER_LINE_COLOR,
                    "id": 2,
                    "label": 'MEDIANA DEI COMUNI ' + cluster.denominazione.upper() + ''
                },

            ]
        }

        return HttpResponse(
            content=json.dumps(
                {
                    "timeSpans": incarichi_set,
                    'data': [cluster_mean_set, voce_set],
                    'legend': legend
                }
            ),
            content_type="application/json"
        )


class IncarichiIndicatoriJSONView(View, IncarichiGetterMixin, IndicatorSlugVerifierMixin):
    def get(self, request, **kwargs):

        # get territorio_opid from GET parameter
        territorio_opid = kwargs['territorio_opid']
        territorio = get_object_or_404(Territorio, op_id=territorio_opid)

        # get indicatori slug from GET parameter
        indicatori_slug_list = self.verify_slug(request.GET.getlist('slug'))
        indicatori = Indicatore.objects.filter(slug__in=indicatori_slug_list)

        if len(indicatori) == 0:
            return HttpResponse()

        incarichi_set = self.get_incarichi_struct(territorio_opid, highlight_color=settings.TERRITORIO_1_COLOR)

        # gets voce value for the territorio over the period set
        indicatori_set = []
        legend_set = []
        for indicator_num, indicatore in enumerate(indicatori):
            indicatori_set.append(self.get_indicatore_struct(territorio, indicatore, line_id=indicator_num,
                                                             line_color=settings.INDICATOR_COLORS[indicator_num]))

            try:
                color = settings.INDICATOR_COLORS[indicator_num]
            except IndexError:
                continue
            else:
                legend_set.append(
                    {
                        "color": color,
                        "id": indicator_num,
                        "label": indicatore.denominazione.upper()
                    }
                )

        return HttpResponse(
            content=json.dumps(
                {
                    "timeSpans": incarichi_set,
                    'data': indicatori_set,
                    'legend': {'title': None, 'items': legend_set}
                }
            ),
            content_type="application/json"
        )


# calculatevariationsmixin
# includes function to calculate voce variations over the years

class CalculateVariationsMixin(object):
    somma_funzioni_affix = '-spese-somma-funzioni'
    # calculates the % variation of main_value compared to comparison_values

    def calculate_variation(self, main_val, comp_val, ):

        if main_val is None or comp_val is None:
            return None

        deflated_main_val = float(main_val)
        deflated_comp_val = float(comp_val)

        if deflated_comp_val != 0 and deflated_main_val != 0:
            # sets 2 digit precision for variation after decimal point
            return round(((deflated_main_val - deflated_comp_val) / deflated_comp_val) * 100.0, 2)
        else:
            # value passes from 0 to N:
            # variation would be infinite so variation is set to null
            return None


    def get_rootnode_slug_entrate(self, bilancio_type, cas_com_type):
        if bilancio_type == "preventivo":
            rootnode_slug = "preventivo-entrate"
        else:
            if cas_com_type == 'cassa':
                rootnode_slug = 'consuntivo-entrate-cassa'
            else:
                rootnode_slug = 'consuntivo-entrate-accertamenti'

        totale_slug = rootnode_slug
        return rootnode_slug, totale_slug


    def get_rootnode_slug_spese(self, bilancio_type, cas_com_type):

        if bilancio_type == "preventivo":
            totale_slug = "preventivo-spese"
        else:
            if cas_com_type == 'cassa':
                totale_slug = bilancio_type + '-spese-cassa'
            else:
                totale_slug = bilancio_type + '-spese-impegni'

        rootnode_slug = totale_slug + self.somma_funzioni_affix

        return rootnode_slug, totale_slug

    def get_slugset_entrate_widget(self, bilancio_type, cas_com_type, widget_type="overview", include_totale=True):

        rootnode_slug, totale_slug = self.get_rootnode_slug_entrate(bilancio_type, cas_com_type)
        rootnode = Voce.objects.get(slug=rootnode_slug)

        if widget_type == 'overview':

            slugset = list(rootnode.get_children().order_by('slug').values_list('slug', flat=True))

        else:
            # gets 1 and 2nd level descendants from root
            slugset = list(
                rootnode.get_descendants(include_self=False).filter(level__lte=rootnode.level + 2).values_list('slug',
                                                                                                               flat=True))

        if include_totale:
            slugset.append(totale_slug)

        return slugset, totale_slug


    def get_slugset_spese_widget(self, bilancio_type, cas_com_type, include_totale=True):

        ##
        # overview widget and spese widget
        ##

        rootnode_slug, totale_slug = self.get_rootnode_slug_spese(bilancio_type, cas_com_type)
        rootnode = Voce.objects.get(slug=rootnode_slug)
        slugset = list(rootnode.get_children().values_list('slug', flat=True))
        slugset.append(totale_slug + '-spese-per-conto-terzi')
        # adds Prestiti and its descendants
        prestiti_descendants = list(
            Voce.objects.get(slug=totale_slug + '-prestiti').get_descendants(include_self=True).values_list('slug',
                                                                                                            flat=True))
        slugset.extend(prestiti_descendants)

        if bilancio_type == 'preventivo':
            slugset.append(totale_slug + '-disavanzo-di-amministrazione')

        if include_totale:
            slugset.append(totale_slug)

        return slugset, totale_slug


    def get_slugset_entrate_chiguadagnaperde(self, bilancio_type, cas_com_type, page_type="overview"):

        rootnode_slug, totale_slug = self.get_rootnode_slug_entrate(bilancio_type, cas_com_type)
        rootnode = Voce.objects.get(slug=rootnode_slug)
        if page_type == 'overview':
            slugset = list(rootnode.get_children().order_by('slug').values_list('slug', flat=True))
        else:
            # gets 1 and 2nd level descendants from root
            descendants = list(
                rootnode.get_descendants(include_self=False).order_by('slug').filter(level__lte=rootnode.level + 2, ))
            slugset = []
            # gets only voce without children
            for d in descendants:
                if d.is_leaf_node():
                    slugset.append(d.slug)

        return slugset


    def get_slugset_spese_chiguadagnaperde(self, bilancio_type, cas_com_type, page_type="overview"):

        ##
        # overview widget and spese widget
        ##

        rootnode_slug, totale_slug = self.get_rootnode_slug_spese(bilancio_type, cas_com_type)
        rootnode = Voce.objects.get(slug=rootnode_slug)
        slugset = list(rootnode.get_children().values_list('slug', flat=True))
        slugset.append(totale_slug + '-prestiti')
        slugset.append(totale_slug + '-spese-per-conto-terzi')

        return slugset


class CompositionWidgetView(CalculateVariationsMixin, TemplateView):
    template_name = None
    show_help = False
    totale_label = "Totale"
    territorio = None
    serie_start_year = settings.APP_START_YEAR
    serie_end_year = settings.APP_END_DATE.year
    widget_type = None
    main_bilancio_year = main_bilancio_type = None
    comp_bilancio_year = comp_bilancio_type = None
    comparison_available = True
    cas_com_type = None

    # data struct for main bilancio / comparison bilancio entrate/spese
    main_regroup_e = None
    main_regroup_s = None
    comp_regroup_e = None
    comp_regroup_s = None

    # slug for total VoceBilancio entrate / spese
    main_tot_e = None
    main_tot_s = None


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


    def calc_variations_set(self, main_dict, comp_dict, ):
        # creates a variations dict based on voce denominazione
        variations = {}
        for main_denominazione, main_value_set in main_dict.iteritems():
            for main_value_dict in main_value_set:
                if main_value_dict['anno'] == self.main_bilancio_year:

                    main_value = main_value_dict['valore']

                    #  gets comparison value for the same voce
                    # checks also for voce with denominazione followed by space: bug

                    main_denominazione_strip = main_denominazione.strip()
                    comparison_value_dict = comp_dict.get(main_denominazione_strip, {})
                    if comparison_value_dict == {}:
                        comparison_value_dict = comp_dict.get(main_denominazione_strip + " ", {})

                    comparison_value_dict = comp_dict.get(main_denominazione, {})

                    comparison_value = comparison_value_dict.get('valore', None)

                    variations[main_denominazione] = \
                        self.calculate_variation(
                            main_value,
                            comparison_value)

        return variations


    def get(self, request, *args, **kwargs):

        ##
        # get params from GET
        # identifies territorio, bilancio yr, bilancio type for main bilancio
        # calculates the best comparison yr and comparison bilancio type
        # set the right template based on widget type
        ##

        self.cas_com_type = self.request.GET.get('cas_com_type', 'cassa')
        self.main_bilancio_year = int(kwargs.get('bilancio_year', settings.APP_END_YEAR))
        self.main_bilancio_type = kwargs.get('bilancio_type', 'consuntivo')
        self.widget_type = kwargs.get('widget_type', 'overview')
        territorio_slug = kwargs.get('territorio_slug', None)

        if not territorio_slug:
            return reverse('404')

        self.territorio = get_object_or_404(Territorio, slug=territorio_slug)

        if self.main_bilancio_year > settings.APP_END_YEAR or\
                self.main_bilancio_year < settings.APP_START_YEAR:
             #     redirect to "bilancio not found"
            return HttpResponseRedirect(reverse('bilancio-not-found'))

        # identifies the bilancio for comparison

        if self.main_bilancio_type == 'preventivo':

            self.comp_bilancio_type = 'consuntivo'
            self.cas_com_type = "cassa"
            verification_voice = self.comp_bilancio_type + '-entrate'
            self.comp_bilancio_year = self.territorio.best_year_voce(year=self.main_bilancio_year - 1,
                                                                     slug=verification_voice)
        else:
            self.comp_bilancio_type = 'preventivo'
            verification_voice = self.comp_bilancio_type + '-entrate'
            self.comp_bilancio_year = self.territorio.best_year_voce(year=self.main_bilancio_year,
                                                                     slug=verification_voice)

        if self.comp_bilancio_year is None:
            self.comparison_available = False

        if self.widget_type == 'overview':
            self.template_name = 'bilanci/composizione_bilancio.html'

        elif self.widget_type == 'entrate' or self.widget_type == 'spese':
            self.template_name = 'bilanci/composizione_entrate_spese.html'
        else:
            return reverse('404')

        return super(CompositionWidgetView, self).get(self, request, *args, **kwargs)


    # return data_regroup for main bilancio over app years
    def get_main_data(self, slugset, totale_slug):

        values = ValoreBilancio.objects.filter(
            voce__slug__in=slugset,
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
            'voce__slug').order_by('voce__denominazione', 'anno')

        main_keygen = lambda x: self.totale_label if x['voce__slug'] == totale_slug else x[
            'voce__denominazione'].strip()
        main_values_regroup = dict((k, list(v)) for k, v in groupby(values, key=main_keygen))

        return main_values_regroup


    # return data_regroup for comp bilancio for comparison year
    def get_comparison_data(self, slugset, totale_slug):

        values = ValoreBilancio.objects.filter(
            voce__slug__in=slugset,
            anno=self.comp_bilancio_year,
            territorio=self.territorio
        ).values('voce__denominazione', 'voce__level', 'anno', 'valore', 'valore_procapite', 'voce__slug').order_by(
            'voce__denominazione', 'anno')

        comp_keygen = lambda x: self.totale_label if x['voce__slug'] == totale_slug else x[
            'voce__denominazione'].strip()
        comp_values_regroup = dict((k, list(v)[0]) for k, v in groupby(values, key=comp_keygen))

        return comp_values_regroup

    def compose_overview_data(self, main_values_regroup, variations):
        composition_data = []

        ##
        # compose_overview_data
        # loops over the results to create the data struct to be returned
        ##

        for main_value_denominazione, main_value_set in main_values_regroup.iteritems():

            # creates value dict
            value_dict = dict(label=main_value_denominazione, series=[], total=False)

            # if the value considered is a total value then sets the appropriate flag
            if main_value_denominazione == self.totale_label:
                value_dict['total'] = True

            # unpacks year values for the considered voice of entrate/spese
            for index, single_value in enumerate(main_value_set):
                value = float(single_value['valore'])
                value_pc = float(single_value['valore_procapite'])

                value_dict['series'].append([single_value['anno'], value])

                if single_value['anno'] == self.main_bilancio_year:
                    value_dict['value'] = round(value, 0)
                    value_dict['procapite'] = value_pc

                    #insert the % of variation between main_bilancio and comparison bilancio
                    value_dict['variation'] = variations[main_value_denominazione]

            composition_data.append(value_dict)

        return composition_data


    def compose_partial_data(self, main_values_regroup, variations, totale_level, ):
        composition_data = []

        ##
        # compose_overview_data
        # loops over the results to create the data struct to be returned
        ##
        for main_value_denominazione, main_value_set in main_values_regroup.iteritems():

            # creates value dict
            value_dict = dict(label=main_value_denominazione, series=[], total=False)

            # insert hierarchy info into the data struct

            # if diff is same level as totale
            if main_value_denominazione != self.totale_label:
                sample_obj = main_value_set[0]

                diff = sample_obj['voce__level'] - totale_level - 1

                # if the voce belongs to somma-funzioni branch then it should
                # be considered one level less than its real level

                if self.somma_funzioni_affix in sample_obj['voce__slug']:
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

            value_dict['andamento'] = 0
            # if the value considered is a total value then sets the appropriate flag
            if main_value_denominazione == self.totale_label:
                value_dict['total'] = True

            # unpacks year values for the considered voice of entrate/spese
            for index, single_value in enumerate(main_value_set):
                value = float(single_value['valore'])
                value_pc = float(single_value['valore_procapite'])

                value_dict['series'].append([single_value['anno'], value])

                if single_value['anno'] == self.main_bilancio_year:
                    value_dict['value'] = round(value, 0)
                    value_dict['procapite'] = value_pc

                    #insert the % of variation between main_bilancio and comparison bilancio
                    value_dict['variation'] = variations[main_value_denominazione]
                    value_dict["variationAbs"] = variations[main_value_denominazione]
                    value_dict["andamento"] = 1

            composition_data.append(value_dict)

        return composition_data


    def get_composition_data(self):
        ##
        # get_composition_data
        # creates composition data to pass to context
        ##


        context = {}
        main_ss_e, self.main_tot_e = self.get_slugset_entrate_widget(self.main_bilancio_type, self.cas_com_type,
                                                                     self.widget_type)
        main_ss_s, self.main_tot_s = self.get_slugset_spese_widget(self.main_bilancio_type, self.cas_com_type)
        comp_ss_e, comp_tot_e = self.get_slugset_entrate_widget(self.comp_bilancio_type, self.cas_com_type,
                                                                self.widget_type)
        comp_ss_s, comp_tot_s = self.get_slugset_spese_widget(self.comp_bilancio_type, self.cas_com_type)

        self.main_regroup_e = self.get_main_data(main_ss_e, self.main_tot_e)
        self.main_regroup_s = self.get_main_data(main_ss_s, self.main_tot_s)

        self.comp_regroup_e = self.get_comparison_data(comp_ss_e, comp_tot_e)
        self.comp_regroup_s = self.get_comparison_data(comp_ss_s, comp_tot_s)

        if self.widget_type == 'entrate':
            # entrate data
            context["type"] = "ENTRATE"
            totale_level = Voce.objects.get(slug=self.main_tot_e).level

            variations_e = self.calc_variations_set(self.main_regroup_e, self.comp_regroup_e, )
            context['composition'] = json.dumps(
                self.compose_partial_data(self.main_regroup_e, variations_e, totale_level))

        elif self.widget_type == 'spese':
            # spese data
            context["type"] = "SPESE"
            totale_level = Voce.objects.get(slug=self.main_tot_s).level

            variations_s = self.calc_variations_set(self.main_regroup_s, self.comp_regroup_s, )
            context['composition'] = json.dumps(
                self.compose_partial_data(self.main_regroup_s, variations_s, totale_level))

        elif self.widget_type == 'overview':
            # entrate data
            variations_e = self.calc_variations_set(self.main_regroup_e, self.comp_regroup_e)

            # spese data
            variations_s = self.calc_variations_set(self.main_regroup_s, self.comp_regroup_s, )

            context['entrate'] = json.dumps(self.compose_overview_data(self.main_regroup_e, variations_e))
            context['spese'] = json.dumps(self.compose_overview_data(self.main_regroup_s, variations_s))

        return context

    def get_widget_data(self):

        context = {}
        e_comp_totale = s_comp_totale = None
        # gets the entrate / spese total values from previous regrouping
        e_main_totale = [x for x in ifilter(lambda emt: emt['anno'] == self.main_bilancio_year,
                                            self.main_regroup_e[self.totale_label])][0]
        s_main_totale = [x for x in ifilter(lambda smt: smt['anno'] == self.main_bilancio_year,
                                            self.main_regroup_s[self.totale_label])][0]

        # three struct for default widget box
        w1 = {'showhelp': self.show_help}
        w2 = {'showhelp': self.show_help}
        w3 = {'showhelp': self.show_help}
        # three struct for circle detail widget box
        w4 = {'showhelp': self.show_help}
        w5 = {'showhelp': self.show_help}
        w6 = {'showhelp': self.show_help}

        e_money_verb, s_money_verb = self.get_money_verb()

        w4['e_moneyverb'] = e_money_verb
        w4["s_moneyverb"] = s_money_verb

        w6["main_bilancio_type_plural"] = self.main_bilancio_type[:-1] + "i"

        if self.comparison_available:

            if len(self.comp_regroup_e):
                e_comp_totale = self.comp_regroup_e[self.totale_label]

            if len(self.comp_regroup_s):
                s_comp_totale = self.comp_regroup_s[self.totale_label]

        # standard entrate totale widget
        entrate_tot = {
            'type': "bar",
            'label': "Entrate - Totale",
            'sublabel1': "",
            'sublabel2': "SUL {0} {1}".format(self.comp_bilancio_type, self.comp_bilancio_year),
            'value': float(e_main_totale['valore']),
            'value_procapite': float(e_main_totale['valore_procapite']),
            'variation': None,
        }
        # standard spese totale widget
        spese_tot = {
            'type': "bar",
            'label': "Spese - Totale",
            'sublabel1': "",
            'sublabel2': "SUL {0} {1}".format(self.comp_bilancio_type, self.comp_bilancio_year),
            'value': float(s_main_totale['valore']),
            'value_procapite': float(s_main_totale['valore_procapite']),
            'variation': None,
        }

        # standard andamento nel tempo widget
        andamento_tempo = {
            'type': "spark",
            'label': "Andamento nel tempo delle entrate",
            'sublabel1': "",
            'sublabel2': "",
            'sublabel3': "{0} nei Bilanci {1} {2}-{3}".format(
                self.widget_type.title() if self.widget_type == 'spese' else 'Entrate',
                self.main_bilancio_type[:-1] + "i",
                settings.APP_START_YEAR,
                settings.APP_END_YEAR
            ),
        }

        surplus = {'type': "surplus",
                   "label": "Avanzo/disavanzo",
                   'sublabel1': "di " + self.cas_com_type,
                   'sublabel2': ""
        }

        # sets variation values if comparison bilancio is available
        if self.comparison_available:
            entrate_tot['variation'] = \
                self.calculate_variation(
                    main_val=e_main_totale['valore'],
                    comp_val=e_comp_totale['valore']
                )
            spese_tot['variation'] = \
                self.calculate_variation(
                    main_val=s_main_totale['valore'],
                    comp_val=s_comp_totale['valore']
                )

        if self.widget_type == 'entrate':

            # widget1 : bar totale entrate
            # widget2: bar totale spese
            w1.update(entrate_tot)
            w2.update(spese_tot)

            # widget3: andamento nel tempo del totale delle entrate
            andamento_tempo['series'] = json.dumps(
                [[v['anno'], v['valore']] for v in self.main_regroup_e[self.totale_label]])
            w3.update(andamento_tempo)

            context['active_layers'] = 2

        elif self.widget_type == 'spese':

            # widget1 : bar totale spese
            # widget2: bar totale entrate
            w1.update(spese_tot)
            w2.update(entrate_tot)

            # widget3: andamento nel tempo del totale delle entrate
            andamento_tempo['label'] = "Andamento nel tempo delle spese"
            andamento_tempo['series'] = json.dumps(
                [[v['anno'], v['valore']] for v in self.main_regroup_s[self.totale_label]])

            w3.update(andamento_tempo)

            context['active_layers'] = 1

        elif self.widget_type == 'overview':

            if self.main_bilancio_type == 'preventivo':

                # widget1 : bar totale entrate
                # widget2: bar totale spese
                w1.update(entrate_tot)
                w2.update(spese_tot)

                # widget3: andamento nel tempo del totale delle entrate
                andamento_tempo['series'] = json.dumps(
                    [[v['anno'], v['valore']] for v in self.main_regroup_e[self.totale_label]])
                w3.update(andamento_tempo)

            else:

                # # creates overview widget data for consuntivo cassa / competenza
                main_consuntivo_spese = [x for x in ifilter(lambda emt: emt['anno'] == self.main_bilancio_year,
                                                            self.main_regroup_s[self.totale_label])][0]
                main_consuntivo_entrate = [x for x in ifilter(lambda emt: emt['anno'] == self.main_bilancio_year,
                                                              self.main_regroup_e[self.totale_label])][0]

                # widget1
                # avanzo / disavanzo di cassa / competenza
                yrs_to_consider = {'1': self.main_bilancio_year - 1, '2': self.main_bilancio_year,
                                   '3': self.main_bilancio_year + 1}

                for k, year in yrs_to_consider.iteritems():
                    if settings.APP_START_YEAR <= year <= settings.APP_END_YEAR:
                        try:
                            entrate = ValoreBilancio.objects.get(anno=year, voce__slug=self.main_tot_e,
                                                                 territorio=self.territorio).valore
                            spese = ValoreBilancio.objects.get(anno=year, voce__slug=self.main_tot_s,
                                                               territorio=self.territorio).valore

                        except ObjectDoesNotExist:
                            continue
                        else:
                            surplus['year' + k] = year
                            surplus['value' + k] = entrate - spese

                w1.update(surplus)
                # variations between consuntivo-entrate and preventivo-entrate / consuntivo-spese and preventivo-spese
                entrate_tot['sublabel1'] = e_money_verb
                spese_tot['sublabel1'] = s_money_verb
                w2.update(entrate_tot)
                w3.update(spese_tot)

        # passing widget data to the context
        context['w1'] = w1
        context['w2'] = w2
        context['w3'] = w3
        context['w4'] = w4
        context['w5'] = w5
        context['w6'] = w6

        return context

    def get_context_data(self, **kwargs):

        context = super(CompositionWidgetView, self).get_context_data(**kwargs)

        ##
        # creates the context to feed the Visup composition widget
        ##

        context['year'] = self.main_bilancio_year

        # gets the circles composition data
        context.update(self.get_composition_data())

        # gets the data to feed to side widgets
        context.update(self.get_widget_data())

        context['comp_bilancio_type'] = self.comp_bilancio_type
        context['comp_bilancio_year'] = self.comp_bilancio_year
        context['main_bilancio_type'] = self.main_bilancio_type
        context['main_bilancio_year'] = self.main_bilancio_year
        context['comparison_bilancio_type'] = self.comp_bilancio_type
        context['comparison_bilancio_year'] = self.comp_bilancio_year
        context['cas_com_type'] = self.cas_com_type
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

        territorio_1 = get_object_or_404(Territorio, op_id=territorio_1_opid)
        territorio_2 = get_object_or_404(Territorio, op_id=territorio_2_opid)

        incarichi_set_1 = self.get_incarichi_struct(territorio_1_opid, highlight_color=territorio_1_color)
        incarichi_set_2 = self.get_incarichi_struct(territorio_2_opid, highlight_color=territorio_2_color)

        if incarichi_set_1 is not None and incarichi_set_2 is not None:

            incarichi_set_1.extend(incarichi_set_2)
            incarichi = incarichi_set_1
        else:
            incarichi = None

        # get voce bilancio from GET parameter
        parameter_slug = kwargs['parameter_slug']
        parameter_type = kwargs['parameter_type']

        if parameter_slug:
            if parameter_type == 'indicatori':
                indicatore = get_object_or_404(Indicatore, slug=parameter_slug)
                # gets indicator value for the territorio over the period set
                data_set_1 = self.get_indicatore_struct(territorio_1, indicatore, line_id=1,
                                                        line_color=territorio_1_color)
                data_set_2 = self.get_indicatore_struct(territorio_2, indicatore, line_id=2,
                                                        line_color=territorio_2_color)

            elif parameter_type == 'entrate' or parameter_type == 'spese-funzioni' or parameter_type == 'spese-interventi':
                voce_bilancio = get_object_or_404(Voce, slug=parameter_slug)
                # gets voce value for the territorio over the period set
                data_set_1 = self.get_voce_struct(territorio_1, voce_bilancio, line_id=1, line_color=territorio_1_color,
                                                  per_capita=True)
                data_set_2 = self.get_voce_struct(territorio_2, voce_bilancio, line_id=2, line_color=territorio_2_color,
                                                  per_capita=True)

            else:
                return reverse('404')

        else:
            return reverse('404')

        legend = [
            {
                "color": territorio_1_color,
                "id": 1,
                "label": u"{0}".format(territorio_1.denominazione)
            },
            {
                "color": territorio_2_color,
                "id": 2,
                "label": u"{0}".format(territorio_2.denominazione)
            },
        ]

        data = [data_set_1, data_set_2]

        return HttpResponse(
            content=json.dumps(
                {
                    "timeSpans": incarichi,
                    'data': data,
                    'legend': {'title': None, 'items': legend}
                }
            ),
            content_type="application/json"
        )


class NotFoundView(TemplateView):
    template_name = "bilanci/not_found.html"


class BilancioNotFoundView(NotFoundView):
    ##
    # show a page when a Comune doesnt have any bilancio
    ##

    def get_context_data(self, **kwargs):
        context = super(BilancioNotFoundView, self).get_context_data(**kwargs)
        context['bilancio'] = True
        return context


class TerritorioNotFoundView(NotFoundView):
    ##
    # show a page when a Comune is not present in the db
    ##
    def get_context_data(self, **kwargs):
        context = super(TerritorioNotFoundView, self).get_context_data(**kwargs)
        context['territorio'] = True
        return context


class BilancioRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):

        # get Territorio data from the request
        try:
            territorio = get_object_or_404(Territorio, slug=self.request.GET.get('territori', 0))
        except Http404:
            return reverse('territorio-not-found')

        kwargs.update({'slug': territorio.slug})

        # redirects to bilancio-overview for the latest bilancio available
        latest_bilancio = territorio.get_latest_bilancio()
        if latest_bilancio is None:
            return reverse('bilancio-not-found')

        anno, tipo_bilancio = latest_bilancio
        try:
            url = reverse('bilanci-overview', args=args, kwargs=kwargs)
        except NoReverseMatch:
            return reverse('territorio-not-found')

        return u"{0}?year={1}&type={2}".format(url, anno, tipo_bilancio)


class BilancioView(DetailView, ServiziComuniMixin, NavigationMenuMixin):
    model = Territorio
    context_object_name = "territorio"
    territorio = None
    servizi_comuni = False

    def get_complete_file(self, file_name):
        """
        Return a dict with file_name and file_size, if a file exists,
        None if the file does not exist.
        """

        file_path = os.path.join(settings.OPENDATA_ZIP_ROOT, file_name)
        if os.path.isfile(file_path):
            file_size = os.stat(file_path).st_size
            return {
                'file_name': file_name,
                'file_size': file_size
            }
        else:
            return {}

    def get_context_data(self, **kwargs):
        context = super(BilancioView, self).get_context_data(**kwargs)

        territorio = self.get_object()
        csv_package_filename = "{0}.zip".format(territorio.cod_finloc)
        context['csv_package_file'] = self.get_complete_file(csv_package_filename)
        context['open_data_url'] = settings.OPENDATA_URL

        future_path = self.request.\
            get_full_path().\
            replace(
                '/bilanci', '/armonizzati/bilanci'
            ).replace(
                'type=consuntivo', 'type=preventivo'
            ).replace(
                'cas_com_type=competenza', 'cas_com_type=cassa'
            ).replace(
                'composizione', 'dettaglio'
            )

        future_path = re.sub(
            r'\?year=[0-9]*',
            '?year=2016',
            future_path
        )

        if 'dettaglio' not in future_path:
            future_path = future_path.replace(
                '/?',
                '/entrate/dettaglio?'
            )

        context['future_path'] = future_path
        context['future_domain'] = self.request.META['HTTP_HOST'].replace(
            'storico.openbilanci.', 'openbilanci.'
        ).replace(
            'storico.staging.openbilanci.', 'staging.openbilanci.'
        )

        context['is_storico'] = 'storico' in self.request.META['HTTP_HOST']

        return context


class BilancioOverView(ShareUrlMixin, CalculateVariationsMixin, BilancioView):
    template_name = 'bilanci/bilancio_overview.html'
    selected_section = "overview"
    accepted_bilancio_types = ['preventivo', 'consuntivo']
    accepted_bilancio_sections = ['entrate', 'spese', 'overview']
    main_bilancio_available = True
    comp_bilancio_available = True
    main_bilancio_year = comp_bilancio_year = None
    main_bilancio_type = comp_bilancio_type = None
    main_bilancio_xml = comp_bilancio_xml = False
    latest_bilancio_tuple = None
    territorio = None
    cas_com_type = None
    fun_int_view = None
    share_url = None

    rootnode_slugs = {
        'preventivo': {
            'entrate': {
                'cassa': 'preventivo-entrate',
                'competenza': 'preventivo-entrate'
            },
            'spese': {
                'cassa': 'preventivo-spese',
                'competenza': 'preventivo-spese'
            },

        },
        'consuntivo': {
            'entrate': {
                'cassa': 'consuntivo-entrate-cassa',
                'competenza': 'consuntivo-entrate-accertamenti'
            },
            'spese': {
                'cassa': 'consuntivo-spese-cassa',
                'competenza': 'consuntivo-spese-impegni'
            }
        }
    }

    def calc_variations_set(self, main_dict, comp_dict, ):
        # creates a variations list of dict based on voce denominazione
        variations = []
        for main_denominazione, main_value_dict in main_dict.iteritems():

            main_value = main_value_dict['valore']

            #  gets comparison value for the same voce
            # checks also for voce with denominazione followed by space: bug

            main_denominazione_strip = main_denominazione.strip()
            comparison_value_dict = comp_dict.get(main_denominazione_strip, {})
            if comparison_value_dict == {}:
                comparison_value_dict = comp_dict.get(main_denominazione_strip + " ", {})

            comparison_value = comparison_value_dict.get('valore', None)

            variation_dict = {
                'slug': main_value_dict['voce__slug'],
                'denominazione': main_denominazione_strip,
                'variation': self.calculate_variation(main_value, comparison_value)
            }

            variations.append(variation_dict)

        return variations

    # return data_regroup for bilancio for selected year
    def get_data(self, slugset, year):

        values = ValoreBilancio.objects.filter(
            voce__slug__in=slugset,
            anno=year,
            territorio=self.territorio
        ).values('voce__denominazione', 'voce__level', 'anno', 'valore', 'valore_procapite', 'voce__slug').order_by(
            'voce__denominazione', 'anno')

        keygen = lambda x: x['voce__denominazione']
        values_regroup = dict((k, list(v)[0]) for k, v in groupby(values, key=keygen))

        return values_regroup

    def get_chi_guardagna_perde(self, value_set, ):
        results = []
        values_not_null = []
        pos_values = []
        neg_values = []
        n_total_elements = 4
        n_half_elements = n_total_elements / 2
        n_negs = 0
        n_pos = 0
        negs_to_add = 2
        pos_to_add = 2

        for value in value_set:
            if value['variation'] is not None:
                if value['variation'] < 0:
                    n_negs += 1
                elif value['variation'] > 0:
                    n_pos += 1

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
                    pos_to_add = n_total_elements - n_negs
                else:
                    pos_to_add = n_pos
                    negs_to_add = n_total_elements - n_pos

        if pos_to_add > 0:
            pos_values = values_not_null[-pos_to_add:]
        if negs_to_add > 0:
            neg_values = values_not_null[:negs_to_add]

        results.extend(pos_values[::-1])
        results.extend(neg_values[::-1])

        # if results < n_total elements, fills in with none values
        if len(results) < n_total_elements:
            diff = n_total_elements - len(results)
            results.extend(repeat(None, diff))

        return results

    def set_comparison_bilancio(self):

        # comp_bilancio_type is the complimentary type of bilancio:
        # if main_bilancio_type is preventivo -> consuntivo
        # and viceversa

        self.comp_bilancio_type = [x for x in self.accepted_bilancio_types if x != self.main_bilancio_type][0]
        verification_voice = self.comp_bilancio_type + '-entrate'

        if self.main_bilancio_type == 'preventivo':
            comparison_year = self.main_bilancio_year - 1
        else:
            comparison_year = self.main_bilancio_year

        self.comp_bilancio_year = self.territorio.best_year_voce(year=comparison_year, slug=verification_voice)

        if self.comp_bilancio_year is None:
            self.comp_bilancio_available = False

    def get_bilancio_url(self):
        # given all the variables, builds the url to redirect the app to the right bilancio page

        querystring = "?year={0}&type={1}&cas_com_type={2}".format(
            self.main_bilancio_year,
            self.main_bilancio_type,
            self.cas_com_type
        )

        if self.selected_section == 'spese' and self.fun_int_view == 'interventi':
            querystring += '&fun_int_view=' + self.fun_int_view

        if not self.servizi_comuni:
            urlconf = None
            redirect_kwargs = {'slug': self.territorio.slug}

            if self.selected_section == 'overview':
                destination_view = 'bilanci-overview'
            else:
                redirect_kwargs['section'] = self.selected_section
                destination_view = "bilanci-{0}".format(self.selected_subsection)

        else:

            urlconf = services.urls
            redirect_kwargs = {}

            if self.selected_section == 'overview':
                destination_view = 'bilanci-overview-services'

            else:
                destination_view = "bilanci-{0}-services".format(self.selected_subsection)
                redirect_kwargs = {'section': self.selected_section}

        return reverse(destination_view, kwargs=redirect_kwargs, urlconf=urlconf) + querystring

    def check_sec_get_params(self):

        ##
        # checks that secondary GET param has an acceptable value. If so Return True, else False
        ##

        if self.main_bilancio_type not in self.accepted_bilancio_types or self.main_bilancio_type is None:
            return False
        if self.selected_section not in self.accepted_bilancio_sections:
            return False
        if self.cas_com_type != 'cassa' and self.cas_com_type != 'competenza':
            return False
        if self.fun_int_view != 'funzioni' and self.fun_int_view != 'interventi':
            return False

        return True

    def get(self, request, *args, **kwargs):

        ##
        # if year or type parameter are missing redirects to a page for default year / default bilancio type
        ##
        redirect_to_latest_bilancio = False
        # check if the request comes from Comuni host
        self.check_servizi_comuni(request)

        # get data from the request
        try:
            self.territorio = self.get_object()
        except Http404:
            return HttpResponseRedirect(reverse('territorio-not-found'))

        # check high-priority parameters: if these params are not present in the request:
        # redirect to latest bilancio for territorio

        self.main_bilancio_year = self.request.GET.get('year', None)
        self.main_bilancio_type = self.request.GET.get('type', None)

        if (
                self.main_bilancio_year is None or
                self.main_bilancio_type is None or
                self.main_bilancio_type not in self.accepted_bilancio_types or
                (
                    isinstance(self.main_bilancio_year, str) is False and
                    isinstance(self.main_bilancio_year, unicode) is False
                )
            ):

            # get latest bilancio, redirect
            latest_tuple = self.territorio.get_latest_bilancio()
            if latest_tuple is None:
                #     redirect to "bilancio not found"
                return HttpResponseRedirect(reverse('bilancio-not-found'))

            self.main_bilancio_year, self.main_bilancio_type = latest_tuple
            redirect_to_latest_bilancio = True

        try:
            self.main_bilancio_year = int(self.main_bilancio_year)
        except ValueError:
            return HttpResponseRedirect(reverse('bilancio-not-found'))

        # if bilancio yr is outside app timeline, redirects to bil.not.found
        if self.main_bilancio_year > settings.APP_END_YEAR or\
                self.main_bilancio_year < settings.APP_START_YEAR:
             #     redirect to "bilancio not found"
            return HttpResponseRedirect(reverse('bilancio-not-found'))

        # check low-priority parameters, forcing default values as fallback
        self.selected_section = kwargs.get('section', 'overview')
        self.fun_int_view = self.request.GET.get('fun_int_view', 'funzioni')

        if self.main_bilancio_type == "preventivo":
            self.cas_com_type = "cassa"
        else:
            self.cas_com_type = self.request.GET.get('cas_com_type', 'cassa')

        if self.check_sec_get_params() is False:
            return HttpResponseRedirect(reverse('bilancio-not-found'))
        ##
        # based on the type of bilancio and the selected section
        # the rootnode slug to check for existance is determined
        ##

        rootnode_slug = self.rootnode_slugs[self.main_bilancio_type]['entrate'][self.cas_com_type]
        if self.selected_section != 'overview':
            rootnode_slug = self.rootnode_slugs[self.main_bilancio_type][self.selected_section][self.cas_com_type]

        # check if select bilancio, year exists:
        # if exists: show bilancio selected section
        # else:
        # if the selected year is APP_END_YEAR or APP_END_YEAR -1: shows bilancio-not-found recente
        #   else: shows bilancio-not-found passato

        try:
            ValoreBilancio.objects.get(voce__slug=rootnode_slug, territorio=self.territorio, anno=self.main_bilancio_year)
        except ObjectDoesNotExist:
            self.main_bilancio_available = False
            self.latest_bilancio_tuple = self.territorio.get_latest_bilancio()

            # get latest bilancio and store it for the context
            # if latest tuple doesn't exists this means the bilancio was set but there is no bilancio in the db
            # for the Comune: so redirect to bilancio not found

            if self.latest_bilancio_tuple is None:
                if self.servizi_comuni:
                #     redirect to "bilancio not found"
                    return HttpResponseRedirect(reverse('bilancio-not-found', urlconf=services.urls))
                else:
                    return HttpResponseRedirect(reverse('bilancio-not-found'))

        # if the request in the query string is incomplete the redirection will be used to have a complete url
        querystring = self.request.META['QUERY_STRING']

        # if the request didn't  have high-priority params: redirect to latest bilancio page
        # if the request didn't have low-priority params: redirect to the page with complete url

        if redirect_to_latest_bilancio or len(querystring.split('&')) < 3:
            # sets querystring, destination view and kwargs parameter for the redirect

            return HttpResponseRedirect(self.get_bilancio_url())

        # identifies the bilancio for comparison
        self.set_comparison_bilancio()

        # check if bilancio main / comparison have been imported from xml file
        self.main_bilancio_xml = ImportXmlBilancio.import_exists(self.territorio, self.main_bilancio_year,
                                                              self.main_bilancio_type)
        self.comp_bilancio_xml = ImportXmlBilancio.import_exists(self.territorio, self.comp_bilancio_year,
                                                              self.comp_bilancio_type)

        return super(BilancioOverView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(BilancioOverView, self).get_context_data(**kwargs)
        query_string = self.request.META['QUERY_STRING']

        context['tipo_bilancio'] = self.main_bilancio_type
        context['selected_bilancio_type'] = self.main_bilancio_type

        self.entrate_kwargs = {'slug': self.territorio.slug, 'section': 'entrate'}
        self.spese_kwargs = {'slug': self.territorio.slug, 'section': 'spese'}

        context['selected_section'] = self.selected_section
        # get Comune context data from db
        territorio_contesto = self.territorio.latest_contesto()
        if territorio_contesto:
            context['bil_popolazione_residente'] = getattr(territorio_contesto, 'bil_popolazione_residente')

        context['territorio_opid'] = self.territorio.op_id
        context['query_string'] = query_string
        context['selected_year'] = str(self.main_bilancio_year)
        context['selector_default_year'] = settings.CLASSIFICHE_END_YEAR
        context['cas_com_type'] = self.cas_com_type

        context['main_bilancio_xml'] = self.main_bilancio_xml
        context['comp_bilancio_xml'] = self.comp_bilancio_xml

        # if servizi_comuni then passes the Pagina Comune data to the template
        if self.servizi_comuni:
            context['pagina_comune'] = self.get_servizi_comune_context()

        if self.main_bilancio_available:

            # chi guadagna / perde

            # entrate data
            main_ss_e = self.get_slugset_entrate_chiguadagnaperde(self.main_bilancio_type, self.cas_com_type,
                                                                  page_type='overview')
            comp_ss_e = self.get_slugset_entrate_chiguadagnaperde(self.comp_bilancio_type, self.cas_com_type,
                                                                  page_type='overview')
            main_regroup_e = self.get_data(main_ss_e, self.main_bilancio_year)
            comp_regroup_e = self.get_data(comp_ss_e, self.comp_bilancio_year)
            variations_e = self.calc_variations_set(main_regroup_e, comp_regroup_e, )
            variations_e_sorted = sorted(variations_e, key=itemgetter('variation'))
            context['entrate_chiguadagnaperde'] = self.get_chi_guardagna_perde(variations_e_sorted)

            # spese data
            main_ss_s = self.get_slugset_spese_chiguadagnaperde(self.main_bilancio_type, self.cas_com_type)
            comp_ss_s = self.get_slugset_spese_chiguadagnaperde(self.comp_bilancio_type, self.cas_com_type)
            main_regroup_s = self.get_data(main_ss_s, self.main_bilancio_year)
            comp_regroup_s = self.get_data(comp_ss_s, self.comp_bilancio_year)
            variations_s = self.calc_variations_set(main_regroup_s, comp_regroup_s, )
            variations_s_sorted = sorted(variations_s, key=itemgetter('variation'))
            context['spese_chiguadagnaperde'] = self.get_chi_guardagna_perde(variations_s_sorted)

            # creates link for voices in chi guadagna/perde based on whether the servizi comune is true
            if self.servizi_comuni:
                context['chiguadagnaperde_entrate_link'] = reverse('bilanci-dettaglio-services',
                                                                   kwargs={'section': 'entrate'}, urlconf=services.urls)
                context['chiguadagnaperde_spese_link'] = reverse('bilanci-dettaglio-services', kwargs={'section': 'spese'},
                                                                 urlconf=services.urls)
            else:
                context['chiguadagnaperde_entrate_link'] = reverse('bilanci-dettaglio', kwargs=self.entrate_kwargs)
                context['chiguadagnaperde_spese_link'] = reverse('bilanci-dettaglio', kwargs=self.spese_kwargs)
        else:

            self.main_bilancio_year, self.main_bilancio_type = self.latest_bilancio_tuple
            context['latest_bilancio_url'] = self.get_bilancio_url()

        context['main_bilancio_available'] = self.main_bilancio_available
        context['comparison_bilancio_type'] = self.comp_bilancio_type
        context['comparison_bilancio_year'] = self.comp_bilancio_year
        context['share_url'] = self.share_url
        context['menu_voices'] = self.get_menu_voices()

        return context


class BilancioComposizioneView(BilancioOverView):
    template_name = 'bilanci/bilancio_composizione.html'
    selected_subsection = 'composizione'

    def get_context_data(self, **kwargs):
        context = super(BilancioComposizioneView, self).get_context_data(**kwargs)
        context['selected_subsection'] = self.selected_subsection

        # chi guadagna / perde
        if self.selected_section == 'entrate':
            # entrate data
            main_ss_e = self.get_slugset_entrate_chiguadagnaperde(self.main_bilancio_type, self.cas_com_type,
                                                                  page_type="entrate")
            comp_ss_e = self.get_slugset_entrate_chiguadagnaperde(self.comp_bilancio_type, self.cas_com_type,
                                                                  page_type="entrate")
            main_regroup_e = self.get_data(main_ss_e, self.main_bilancio_year)
            comp_regroup_e = self.get_data(comp_ss_e, self.comp_bilancio_year)
            variations_e = self.calc_variations_set(main_regroup_e, comp_regroup_e, )
            variations_e_sorted = sorted(variations_e, key=itemgetter('variation'))
            context['chiguadagnaperde'] = self.get_chi_guardagna_perde(variations_e_sorted)
        else:
            # spese data
            main_ss_s = self.get_slugset_spese_chiguadagnaperde(self.main_bilancio_type, self.cas_com_type)
            comp_ss_s = self.get_slugset_spese_chiguadagnaperde(self.comp_bilancio_type, self.cas_com_type)
            main_regroup_s = self.get_data(main_ss_s, self.main_bilancio_year)
            comp_regroup_s = self.get_data(comp_ss_s, self.comp_bilancio_year)
            variations_s = self.calc_variations_set(main_regroup_s, comp_regroup_s, )
            variations_s_sorted = sorted(variations_s, key=itemgetter('variation'))
            context['chiguadagnaperde'] = self.get_chi_guardagna_perde(variations_s_sorted)

        if self.servizi_comuni:
            context['chiguadagnaperde_link'] = reverse('bilanci-dettaglio-services',
                                                       kwargs={'section': self.selected_section}, urlconf=services.urls)
        else:
            context['chiguadagnaperde_link'] = reverse('bilanci-dettaglio', kwargs=self.spese_kwargs)

        return context


class BilancioDettaglioView(BilancioOverView):
    model = Territorio

    template_name = 'bilanci/bilancio_dettaglio.html'
    selected_subsection = 'dettaglio'

    def get_slug(self):
        cassa_competenza_type = self.cas_com_type
        if self.cas_com_type == 'competenza':
            if self.selected_section == 'entrate':
                cassa_competenza_type = 'accertamenti'
            else:
                cassa_competenza_type = 'impegni'

        if self.main_bilancio_type == 'preventivo':
            return "{0}-{1}".format(
                self.main_bilancio_type,
                self.selected_section
            )
        else:
            return "{0}-{1}-{2}".format(
                self.main_bilancio_type,
                self.selected_section,
                cassa_competenza_type
            )

    def get_context_data(self, **kwargs):

        context = super(BilancioDettaglioView, self).get_context_data(**kwargs)
        query_string = self.request.META['QUERY_STRING']
        voce_slug = self.get_slug()

        # checks if political context data is available to show/hide timeline widget in the template
        context['show_timeline'] = True
        incarichi_set = Incarico.objects.filter(territorio=self.territorio)
        if len(incarichi_set) == 0:
            context['show_timeline'] = False

        if self.main_bilancio_available:
            # gets the tree structure from db
            bilancio_rootnode = Voce.objects.get(slug=voce_slug)

            # gets the part of bilancio data which is referring to Voce nodes which are
            # descendants of bilancio_treenodes to minimize queries and data size
            budget_values = ValoreBilancio.objects.filter(territorio=self.territorio, anno=self.main_bilancio_year). \
                filter(voce__in=bilancio_rootnode.get_descendants(include_self=True).values_list('pk', flat=True))

            absolute_values = budget_values.values_list('voce__slug', 'valore')
            percapita_values = budget_values.values_list('voce__slug', 'valore_procapite')

            absolute_values = dict(
                map(
                    lambda x: (x[0], x[1]),
                    absolute_values
                )
            )
            percapita_values = dict(
                map(
                    lambda x: (x[0], x[1]),
                    percapita_values
                )
            )

            context['budget_values'] = {
                'absolute': dict(absolute_values),
                'percapita': dict(percapita_values)
            }

            # arranges the bilancio_tree to have the voce in the desired order: first the voce with children,
            # then the leaves somma funzioni needs a special treatment because the denominazione starts with "_"
            # which puts all the branch at the end of the alphabetical order

            if self.selected_section == 'spese' and self.fun_int_view == 'funzioni':
                if self.main_bilancio_type == 'consuntivo':
                    if self.cas_com_type == 'cassa':
                        base_slug = 'consuntivo-spese-cassa'
                    else:
                        base_slug = 'consuntivo-spese-impegni'
                else:
                    base_slug = 'preventivo-spese'

                somma_funzioni = list(
                    Voce.objects.get(slug="{0}-spese-somma-funzioni".format(base_slug)).get_descendants(include_self=True))
                prestiti = list(Voce.objects.get(slug="{0}-prestiti".format(base_slug)).get_descendants(include_self=True))
                spese_conto_terzi = list(
                    Voce.objects.get(slug="{0}-spese-per-conto-terzi".format(base_slug)).get_descendants(include_self=True))

                bilancio_tree = somma_funzioni
                bilancio_tree.extend(prestiti)
                bilancio_tree.extend(spese_conto_terzi)

                if self.main_bilancio_type == 'preventivo':
                    disavanzo = list(
                        Voce.objects.get(slug="{0}-disavanzo-di-amministrazione".format(base_slug)).get_descendants(
                            include_self=True))
                    bilancio_tree.extend(disavanzo)
            else:
                bilancio_tree = bilancio_rootnode.get_descendants(include_self=False)
                first_level_voci = bilancio_tree.filter(level=bilancio_rootnode.level + 1, children__isnull=True)
                bilancio_tree = list(bilancio_tree.exclude(level=bilancio_rootnode.level + 1, children__isnull=True))
                bilancio_tree.extend(first_level_voci)

            context['bilancio_rootnode'] = bilancio_rootnode
            context['bilancio_tree'] = bilancio_tree

            # get link for classifiche to insert in the accordion
            if self.main_bilancio_type == 'consuntivo':
                if self.selected_section == 'spese':
                    if self.fun_int_view == 'funzioni':

                        context['classifiche_allowed_params'] = HierarchicalMenuMixin.get_classifiche_parameters()[
                            'spese_funzioni']
                    else:
                        context['classifiche_allowed_params'] = HierarchicalMenuMixin.get_classifiche_parameters()[
                            'spese_interventi']
                else:
                    context['classifiche_allowed_params'] = HierarchicalMenuMixin.get_classifiche_parameters()['entrate']

            if self.selected_section == 'spese':
                # Extend the context with funzioni/interventi view and switch variables

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

        context['link_to_classifiche_available'] = False
        if self.main_bilancio_type == 'consuntivo' and settings.CLASSIFICHE_START_YEAR <= self.main_bilancio_year <= settings.CLASSIFICHE_END_YEAR:
            context['link_to_classifiche_available'] = True

        context['query_string'] = query_string
        context['year'] = self.main_bilancio_year
        context['bilancio_type'] = self.main_bilancio_type
        context['bilancio_type_title'] = self.main_bilancio_type[:-1] + "i"
        context['selected_subsection'] = self.selected_subsection

        return context


class BilancioIndicatoriView(ShareUrlMixin, MiniClassificheMixin, BilancioView, IndicatorSlugVerifierMixin):
    model = Territorio
    context_object_name = "territorio"
    template_name = 'bilanci/bilancio_indicatori.html'
    selected_section = "indicatori"
    share_url = None
    territorio = None
    entrate_kwargs = None
    spese_kwargs = None

    def get(self, request, *args, **kwargs):

        ##
        # if parameter is missing redirects to a page for default indicator
        ##

        self.territorio = self.get_object()

        if ValoreIndicatore.objects.filter(territorio=self.territorio).count() == 0:
            return HttpResponseRedirect(reverse('404'))

        # check if the request comes from Comuni host
        self.check_servizi_comuni(request)

        if self.request.GET.get('slug') is None:
            urlconf = None
            destination_view = 'bilanci-indicatori'
            kwargs = {'slug': self.territorio.slug}
            if self.servizi_comuni:
                destination_view = 'bilanci-indicatori-services'
                urlconf = services.urls
                kwargs = None

            return HttpResponseRedirect(reverse(destination_view, kwargs=kwargs, urlconf=urlconf) \
                                        + "?slug={0}".format(settings.DEFAULT_INDICATOR_SLUG))

        return super(BilancioIndicatoriView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(BilancioIndicatoriView, self).get_context_data(**kwargs)

        self.entrate_kwargs = {'slug': self.territorio.slug, 'section': 'entrate'}
        self.spese_kwargs = {'slug': self.territorio.slug, 'section': 'spese'}

        # get selected indicatori slug list from request and verifies them
        selected_indicators_slugs = self.verify_slug(self.request.GET.getlist('slug'))

        context['selected_section'] = self.selected_section

        last_indicatore_yr = self.territorio.latest_year_indicatore(slug=settings.DEFAULT_INDICATOR_SLUG)
        if last_indicatore_yr:
            context['incarichi_attivi'] = Incarico.get_incarichi_attivi(territorio=self.territorio,
                                                                        anno=last_indicatore_yr)
            context['last_indicatore_yr'] = last_indicatore_yr
            context['indicatore_position'] = self.get_indicatore_positions(territorio=self.territorio,
                                                                           anno=last_indicatore_yr)

        # if servizi_comuni then passes the header/footer text to the template
        if self.servizi_comuni:
            context['pagina_comune'] = self.get_servizi_comune_context()

        # get Comune context data from db
        territorio_contesto = self.territorio.latest_contesto()
        if territorio_contesto:
            context['bil_popolazione_residente'] = getattr(territorio_contesto, 'bil_popolazione_residente')

        context['territorio_opid'] = self.territorio.op_id
        context['territorio_cluster'] = Territorio.objects.get(territorio=Territorio.TERRITORIO.L,
                                                               cluster=self.territorio.cluster).denominazione
        context['n_comuni_cluster'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.C,
                                                                cluster=self.territorio.cluster).count()
        context['selected_cluster_str'] = str(self.territorio.cluster)
        context['selected_regioni_str'] = ",".join([str(k) for k in list(
            Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).values_list('pk', flat=True))])
        context['menu_voices'] = self.get_menu_voices()
        context['indicator_list'] = Indicatore.objects.filter(published=True).order_by('denominazione')

        # creates the query string to call the IncarichiIndicatori Json view in template
        context['selected_indicators'] = selected_indicators_slugs
        context['selected_indicators_qstring'] = '?slug=' + '&slug='.join(selected_indicators_slugs)
        context['share_url'] = self.share_url

        context['import_xml'] = ImportXmlBilancio.has_xml_import(self.territorio)
        return context


class ClassificheRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):

        # redirects to Classifiche starting page when coming from navbar
        kwargs['parameter_type'] = 'entrate'
        kwargs['parameter_slug'] = settings.DEFAULT_VOCE_SLUG_CLASSIFICHE
        kwargs['anno'] = settings.CLASSIFICHE_END_YEAR

        try:
            url = reverse('classifiche-list', args=args, kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url


class ClassificheSearchView(MiniClassificheMixin, RedirectView):
    paginate_by = settings.CLASSIFICHE_PAGINATE_BY

    def get(self, request, *args, **kwargs):
        ##
        # catches the user search for a territorio,
        # redirects to the correct classifiche list page highlighting the chosen territorio
        ##

        territorio_found = True

        selected_cluster = request.GET.get('selected_cluster', '').split(',')

        # if no region is selected, they are all selected
        all_regions = Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).values_list('pk', flat=True)
        all_regions_str = ','.join([str(pk) for pk in all_regions])

        selected_regioni = request.GET.get('selected_regioni', all_regions_str).split(',')

        selected_par_type = request.GET.get('selected_par_type')
        selected_parameter_id = request.GET.get('selected_parameter_id')
        territorio_id = request.GET.get('territorio_id', None)
        if not territorio_id:
            return HttpResponseRedirect(reverse('classifiche-redirect'))

        territorio_id = int(territorio_id)
        selected_year = request.GET.get('selected_year')

        selected_regioni_names = Territorio.objects.filter(pk__in=selected_regioni).values_list('denominazione',
                                                                                                flat=True)

        territori_baseset = list(
            Territorio.objects.filter(cluster__in=selected_cluster, regione__in=selected_regioni_names).values_list(
                'pk', flat=True))

        # gets the selected parameter: voce or indicatore
        # if the parameter does NOT exist (wrong parameter) redirects to classifiche home page
        if selected_par_type == 'indicatori':
            all_ids_values = ValoreIndicatore.objects.get_classifica_ids(selected_parameter_id, selected_year)
            try:
                parameter_slug = Indicatore.objects.get(pk=selected_parameter_id).slug
            except ObjectDoesNotExist:
                return HttpResponseRedirect(reverse('classifiche-redirect'))
        else:
            all_ids_values = ValoreBilancio.objects.get_classifica_ids(selected_parameter_id, selected_year)
            try:
                parameter_slug = Voce.objects.get(pk=selected_parameter_id).slug
            except ObjectDoesNotExist:
                return HttpResponseRedirect(reverse('classifiche-redirect'))

        # calculate territorio page
        try:
            territorio_idx = [element['territorio__id'] for element in all_ids_values if
                              element['territorio__id'] in territori_baseset].index(territorio_id)
            territorio_page = (territorio_idx / self.paginate_by) + 1
        except ValueError:
            territorio_page = 1
            territorio_found = False

        kwargs['parameter_type'] = selected_par_type
        kwargs['parameter_slug'] = parameter_slug
        kwargs['anno'] = selected_year

        try:
            url = reverse('classifiche-list', args=args, kwargs=kwargs) + \
                  '?' + "r=" + "&r=".join(selected_regioni) + "&c=" + "&c=".join(selected_cluster) + '&page=' + str(
                territorio_page)

            if territorio_found:
                url += '&hl=' + str(territorio_id)
        except NoReverseMatch:
            url = reverse('404')

        return HttpResponseRedirect(url)

    def get_redirect_url(self, *args, **kwargs):
        if True:
            pass
        pass


class ClassificheListView(HierarchicalMenuMixin, MiniClassificheMixin, ListView):
    template_name = 'bilanci/classifiche.html'
    paginate_by = settings.CLASSIFICHE_PAGINATE_BY
    n_comuni = None
    parameter_type = None
    parameter = None
    anno = None
    anno_int = None
    reset_pages = False
    curr_ids = None
    selected_regioni = []
    selected_cluster = []
    positions = {}
    prev_positions = {}
    curr_year = None
    prev_year = None

    def get(self, request, *args, **kwargs):

        # checks that parameter type is correct
        # checks that parameter slug exists

        self.parameter_type = kwargs['parameter_type']
        parameter_slug = kwargs['parameter_slug']

        if self.parameter_type == 'indicatori':
            self.parameter = get_object_or_404(Indicatore, slug=parameter_slug)
        elif self.parameter_type == 'entrate' or self.parameter_type == 'spese-interventi' or self.parameter_type == 'spese-funzioni':
            self.parameter = get_object_or_404(Voce, slug=parameter_slug)
        else:
            return HttpResponseRedirect(reverse('404'))

        self.anno = kwargs['anno']
        self.anno_int = int(self.anno)

        # if anno is out of range -> redirects to the latest yr for classifiche
        if self.anno_int > settings.CLASSIFICHE_END_YEAR or self.anno_int < settings.CLASSIFICHE_START_YEAR:
            return HttpResponseRedirect(reverse('classifiche-list', kwargs={'parameter_type': self.parameter_type,
                                                                            'parameter_slug': self.parameter.slug,
                                                                            'anno': settings.CLASSIFICHE_END_YEAR}))

        # this try / except block is needed to prevent multiple requests from malicious bots
        try:
            selected_regioni_get = [int(k) for k in self.request.GET.getlist('r')]
        except ValueError:
            return HttpResponseBadRequest()

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
            curr_id_values_all = ValoreIndicatore.objects.get_classifica_ids(self.parameter.id, self.curr_year)
            prev_id_values_all = ValoreIndicatore.objects.get_classifica_ids(self.parameter.id, self.prev_year)
        else:
            curr_id_values_all = ValoreBilancio.objects.get_classifica_ids(self.parameter.id, self.curr_year)
            prev_id_values_all = ValoreBilancio.objects.get_classifica_ids(self.parameter.id, self.prev_year)

        # gets only the territorio__id in the right order
        curr_id_all = [k['territorio__id'] for k in curr_id_values_all]

        ##
        # Filters on regioni / cluster
        ##

        # initial territori_baseset is the complete list of comuni
        territori_baseset = Territorio.objects.comuni

        if len(self.selected_regioni):
            # this passege is necessary because in the regione field of territorio there is the name of the region
            selected_regioni_names = list(
                Territorio.objects.regioni.filter(pk__in=self.selected_regioni).values_list('denominazione', flat=True)
            )
            territori_baseset = territori_baseset.filter(regione__in=selected_regioni_names)

        if len(self.selected_cluster):
            territori_baseset = territori_baseset.filter(cluster__in=self.selected_cluster)

        territori_ids = list(territori_baseset.values_list('id', flat=True))

        # gets all the ids of the territori selected filtering the whole set
        self.curr_ids = [id for id in curr_id_all if id in territori_ids]

        self.positions = self.get_positions(curr_id_values_all, territori_ids)
        self.prev_positions = self.get_positions(prev_id_values_all, territori_ids)
        self.queryset = self.curr_ids
        return self.queryset

    def get_context_data(self, **kwargs):

        # enrich the Queryset in object_list with Political context data and variation value
        object_list = []
        page = int(self.request.GET.get('page', 1))

        paginator_offset = ((page - 1) * self.paginate_by) + 1

        all_regions = Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).values_list('pk', flat=True)
        all_clusters = Territorio.objects.filter(territorio=Territorio.TERRITORIO.L).values_list('cluster', flat=True)

        context = super(ClassificheListView, self).get_context_data(**kwargs)

        # creates context data based on the paginated queryset
        paginated_queryset = context['object_list']

        # regroups incarichi politici based on territorio
        incarichi_set = Incarico.get_incarichi_attivi_set(paginated_queryset, self.curr_year).select_related(
            'territorio')
        incarichi_territorio_keygen = lambda x: x.territorio.pk
        incarichi_regroup = dict((k, list(v)) for k, v in groupby(incarichi_set, key=incarichi_territorio_keygen))

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
            try:
                obj = objects_dict[territorio_id]
            except KeyError:
                continue

            if self.parameter_type == 'indicatori':
                valore = obj.valore

            else:
                valore = obj.valore_procapite

            if territorio_id in incarichi_regroup.keys():
                incarichi = incarichi_regroup[territorio_id]

            position = None
            prev_position = None
            if territorio_id in self.positions:
                position = self.positions[territorio_id]

            if territorio_id in self.prev_positions:
                prev_position = self.prev_positions[territorio_id]

            territorio_dict = {
                'territorio': {
                    'denominazione': obj.territorio.denominazione,
                    'slug': obj.territorio.slug,
                    'prov': obj.territorio.prov,
                    'regione': obj.territorio.regione,
                    'pk': obj.territorio.pk,
                    'import_xml': len(obj.territorio.importxmlbilancio_set.filter(tipologia="consuntivo", anno=self.curr_year)) > 0
                },
                'valore': valore,
                'variazione': 0,
                'incarichi_attivi': incarichi,
                'position': position,
                'prev_position': prev_position,
            }

            # adjust prev position and variation if values are found
            if territorio_id in self.positions and territorio_id in self.prev_positions:
                territorio_dict['variazione'] = self.prev_positions[territorio_id] - self.positions[territorio_id]

            object_list.append(territorio_dict)

        # updates obj list
        context['object_list'] = object_list
        context['n_comuni'] = len(self.queryset)

        # defines the lists of possible confrontation parameters
        context['selected_par_type'] = self.parameter_type
        context['selected_parameter'] = self.parameter
        context['selected_parameter_name'] = self.parameter.denominazione

        self.selected_regioni = list(self.selected_regioni) if len(self.selected_regioni) > 0 else list(all_regions)
        self.selected_cluster = list(self.selected_cluster) if len(self.selected_cluster) > 0 else list(all_clusters)

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

        # get parameter list for hierarchical menu
        context['parameter_list'] = self.get_parameter_struct()

        context['regioni_list'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).order_by(
            'denominazione')
        context['cluster_list'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.L).order_by('-cluster')
        context['territori_search_form_classifiche'] = TerritoriSearchFormClassifiche()
        context['query_string'] = "r=" + "&r=".join(selected_regioni_str) + "&c=" + "&c=".join(selected_cluster_str)

        # if there is a territorio to highlight passes the data to context
        context['highlight_territorio'] = None
        territorio_highlight = self.request.GET.get('hl', None)

        if territorio_highlight is not None:
            context['highlight_territorio'] = int(territorio_highlight)

        # creates url for share button
        regioni_list = ['', ]
        regioni_list.extend([str(r) for r in self.selected_regioni])
        cluster_list = ['', ]
        cluster_list.extend(self.selected_cluster)

        # gets current page url
        long_url = self.request.build_absolute_uri(
            reverse('classifiche-list', kwargs={'anno': self.anno, 'parameter_type': self.parameter_type,
                                                'parameter_slug': self.parameter.slug})
        ) + '?' + "&r=".join(regioni_list) + "&c=".join(cluster_list) + '&page=' + str(context['page_obj'].number)
        # checks if short url is already in the db, otherwise asks to google to shorten the url

        short_url_obj = None
        try:
            short_url_obj = ShortUrl.objects.get(long_url=long_url)
        except MultipleObjectsReturned:
            short_url_obj = ShortUrl.objects.filter(long_url=long_url)[0]

        except ObjectDoesNotExist:

            payload = {'longUrl': long_url + '&key=' + settings.GOOGLE_SHORTENER_API_KEY}
            headers = {'content-type': 'application/json'}
            try:
                short_url_req = requests.post(settings.GOOGLE_SHORTENER_URL, data=json.dumps(payload), headers=headers)
                if short_url_req.status_code == requests.codes.ok:
                    short_url = short_url_req.json().get('id')
                    short_url_obj = ShortUrl()
                    short_url_obj.short_url = short_url
                    short_url_obj.long_url = long_url
                    short_url_obj.save()
            except (ConnectionError, Timeout, SSLError, ProxyError):
                logger.warning("Error connecting with Google url shortener service")

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

        context = {'territori_comparison_search_form': TerritoriComparisonSearchForm(), }

        return context


class ConfrontiRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):

        # redirects to appropriate confronti view based on default parameter for Territori
        kwargs['parameter_slug'] = settings.DEFAULT_VOCE_SLUG_CONFRONTI

        try:
            url = reverse('confronti-entrate', args=args, kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url


class ConfrontiView(ShareUrlMixin, HierarchicalMenuMixin, TemplateView):
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

        self.territorio_1 = get_object_or_404(Territorio, slug=territorio_1_slug)
        self.territorio_2 = get_object_or_404(Territorio, slug=territorio_2_slug)

        return super(ConfrontiView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # construct common context data for Confronti View
        context = super(ConfrontiView, self).get_context_data(**kwargs)

        context['territorio_1'] = self.territorio_1
        context['territorio_2'] = self.territorio_2

        context['territorio_1_import_xml'] = ImportXmlBilancio.has_xml_import(self.territorio_1)
        context['territorio_2_import_xml'] = ImportXmlBilancio.has_xml_import(self.territorio_2)

        context['contesto_1'] = self.territorio_1.latest_contesto
        context['contesto_2'] = self.territorio_2.latest_contesto

        context['parameter_list'] = self.get_parameter_struct()
        context['share_url'] = self.share_url
        context['territori_comparison_search_form'] = \
            TerritoriComparisonSearchForm(
                initial={
                    'territorio_1': self.territorio_1,
                    'territorio_2': self.territorio_2
                }
            )

        return context


class ConfrontiBilancioView(ConfrontiView):
    def get_context_data(self, **kwargs):
        context = super(ConfrontiBilancioView, self).get_context_data(**kwargs)
        context['selected_par_type'] = self.get_parameter_type()
        selected_parameter = get_object_or_404(Voce, slug=kwargs['parameter_slug'])
        context['selected_parameter'] = selected_parameter

        context['selected_parameter_name'] = selected_parameter.denominazione
        if selected_parameter.slug == 'consuntivo-spese-cassa':
            context['selected_parameter_name'] = u'Totale spese'
        elif selected_parameter.slug == 'consuntivo-entrate-cassa':
            context['selected_parameter_name'] = u'Totale entrate'
        elif selected_parameter.slug == 'consuntivo-spese-cassa-spese-somma-funzioni':
            context['selected_parameter_name'] = u'FUNZIONI'
        elif selected_parameter.slug == 'consuntivo-spese-cassa-spese-per-investimenti-interventi':
            context['selected_parameter_name'] = u'Interventi - Spese per investimenti'
        elif selected_parameter.slug == 'consuntivo-spese-cassa-spese-correnti-interventi':
            context['selected_parameter_name'] = u'Interventi - Spese correnti'

        return context


class ConfrontiEntrateView(ConfrontiBilancioView):
    def get_parameter_type(self):
        return 'entrate'


class ConfrontiSpeseInterventiView(ConfrontiBilancioView):
    def get_parameter_type(self):
        return 'spese-interventi'


class ConfrontiSpeseFunzioniView(ConfrontiBilancioView):
    def get_parameter_type(self):
        return 'spese-funzioni'


class ConfrontiIndicatoriView(ConfrontiView, MiniClassificheMixin):
    def get_context_data(self, **kwargs):
        context = super(ConfrontiIndicatoriView, self).get_context_data(**kwargs)
        context['selected_par_type'] = "indicatori"
        selected_parameter = get_object_or_404(Indicatore, slug=kwargs['parameter_slug'])
        context['selected_parameter'] = selected_parameter
        context['selected_parameter_name'] = selected_parameter.denominazione
        context['territorio_1_cluster'] = Territorio.objects.get(territorio=Territorio.TERRITORIO.L,
                                                                 cluster=self.territorio_1.cluster).denominazione
        context['territorio_2_cluster'] = Territorio.objects.get(territorio=Territorio.TERRITORIO.L,
                                                                 cluster=self.territorio_2.cluster).denominazione

        context['n_comuni_cluster_1'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.C,
                                                                  cluster=self.territorio_1.cluster).count()
        context['selected_cluster_str_1'] = str(self.territorio_1.cluster)
        context['n_comuni_cluster_2'] = Territorio.objects.filter(territorio=Territorio.TERRITORIO.C,
                                                                  cluster=self.territorio_2.cluster).count()
        context['selected_cluster_str_2'] = str(self.territorio_2.cluster)

        context['selected_regioni_str'] = ",".join([str(k) for k in list(
            Territorio.objects.filter(territorio=Territorio.TERRITORIO.R).values_list('pk', flat=True))])

        # construct data for miniclassifiche
        last_indicatore_yr_1 = self.territorio_1.latest_year_indicatore(slug='autonomia-finanziaria')
        last_indicatore_yr_2 = self.territorio_2.latest_year_indicatore(slug='autonomia-finanziaria')

        if last_indicatore_yr_2 and last_indicatore_yr_1:
            # if there is valid data for miniclassifiche, adds the data to the context

            last_indicatore_yr = last_indicatore_yr_1
            if last_indicatore_yr_1 > last_indicatore_yr_2:
                last_indicatore_yr = last_indicatore_yr_2

            context['last_indicatore_yr'] = last_indicatore_yr
            context['indicatore_positions_1'] = self.get_indicatore_positions(territorio=self.territorio_1,
                                                                              anno=last_indicatore_yr)
            context['indicatore_positions_2'] = self.get_indicatore_positions(territorio=self.territorio_2,
                                                                              anno=last_indicatore_yr)
            context['incarichi_attivi_1'] = Incarico.get_incarichi_attivi(territorio=self.territorio_1,
                                                                          anno=last_indicatore_yr)
            context['incarichi_attivi_2'] = Incarico.get_incarichi_attivi(territorio=self.territorio_2,
                                                                          anno=last_indicatore_yr)

        return context


class PageNotFoundTemplateView(TemplateView):
    template_name = '404.html'



