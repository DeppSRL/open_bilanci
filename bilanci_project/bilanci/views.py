import re
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, RedirectView, View, ListView
import json
from bilanci.forms import TerritoriComparisonSearchForm
from bilanci.models import ValoreBilancio, Voce, Indicatore, ValoreIndicatore
from django.http.response import HttpResponse, HttpResponseRedirect
from bilanci.utils import couch
from collections import OrderedDict
from django.conf import settings

from territori.models import Territorio, Contesto, Incarico


class HomeView(TemplateView):
    template_name = "home.html"


class IncarichiGetterMixin(object):
    
    date_fmt = '%Y-%m-%d'
            
    #     sets the start / end of graphs 
    timeline_start = settings.GRAPH_START_DATE
    timeline_end = settings.GRAPH_END_DATE
    
    def transform_incarichi(self, incarichi_set, highlight_color):

        incarichi_transformed = []
        for incarico in incarichi_set:

            dict_widget = {
                'start':  incarico.data_inizio.strftime(self.date_fmt),
                'end': incarico.data_fine.strftime(self.date_fmt),

                # sets incarico marker color and highlight
                'color': settings.INCARICO_MARKER_INACTIVE,
                'highlightColor': highlight_color,
            }

            if incarico.is_commissario:
                # commissari

                dict_widget['label'] = "Commissariamento".upper()
                dict_widget['icon'] = settings.INCARICO_MARKER_DUMMY
                dict_widget['sublabel'] = incarico.motivo_commissariamento

            else :
                # sindaci

                # sets sindaco name, surname
                dict_widget['label'] = "{0}.{1}".\
                    format(
                        incarico.nome[0].upper(),
                        incarico.cognome.upper().encode('utf-8'),
                    )

                dict_widget['icon'] = settings.INCARICO_MARKER_DUMMY
                if incarico.pic_url:
                    dict_widget['icon'] = incarico.pic_url


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

    def get_voce_struct(self, territorio, voce_bilancio, line_id, line_color):

        voce_values = ValoreBilancio.objects.filter(
            territorio = territorio,
            voce = voce_bilancio,
            anno__gte = self.timeline_start.tm_year,
            anno__lte = self.timeline_end.tm_year
        ).order_by('anno')

        return self.transform_voce(voce_values, line_id, line_color)

    ##
    # get indicatori values of specified Indicatore for Territorio in the time span
    ##

    def get_indicatore_struct(self, territorio, indicatore, line_id, line_color):

        indicatore_values = ValoreIndicatore.objects.filter(
            territorio = territorio,
            indicatore = indicatore,
            anno__gte = self.timeline_start.tm_year,
            anno__lte = self.timeline_end.tm_year
        ).order_by('anno')

        return self.transform_voce(indicatore_values, line_id, line_color)


class IncarichiVociJSONView(View, IncarichiGetterMixin):
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
        voce_set = self.get_voce_struct(territorio, voce_bilancio, line_id=1, line_color=settings.TERRITORIO_1_COLOR)

        cluster_mean_set = self.get_voce_struct(cluster, voce_bilancio, line_id=2, line_color=settings.CLUSTER_LINE_COLOR)

        legend = [
            {
              "color": settings.TERRITORIO_1_COLOR,
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
                data_set_1 = self.get_voce_struct(territorio_1, voce_bilancio, line_id=1, line_color = territorio_1_color)
                data_set_2 = self.get_voce_struct(territorio_2, voce_bilancio, line_id=2, line_color = territorio_2_color)

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
        budget_values = ValoreBilancio.objects.filter(territorio = territorio, anno=year).\
            filter(voce__in=bilancio_rootnode.get_descendants(include_self=True).values_list('pk', flat=True))

        context['budget_values'] = {
            'absolute': dict(budget_values.values_list('voce__slug', 'valore')),
            'percapita': dict(budget_values.values_list('voce__slug', 'valore_procapite'))
        }

        menu_voices_kwargs = {'slug': territorio.slug}

        # checks if political context data is available to show/hide timeline widget in the template
        context['show_timeline'] = True
        incarichi_set = Incarico.objects.filter(territorio=Territorio.objects.get(op_id=territorio.op_id))
        if len(incarichi_set) == 0:
            context['show_timeline'] = False


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
        type = self.request.GET['type']
        if type == 'preventivo':
            return "{0}-{1}".format(self.request.GET['type'],"spese")
        else:
            return "{0}-{1}".format(self.request.GET['type'],"spese-impegni")

class BilancioIndicatoriView(BilancioView):
    template_name = 'bilanci/indicatori.html'



class ClassificheRedirectView(RedirectView):

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

class ClassificheListView(ListView):

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
        # todo: define in settings default indicator
        kwargs['parameter_slug'] = Indicatore.objects.all()[0].slug

        try:
            url = reverse('confronti-indicatori', args=args , kwargs=kwargs)
        except NoReverseMatch:
            return reverse('404')
        else:
            return url


class ConfrontiView(TemplateView):

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


