from django.contrib.sitemaps import Sitemap, GenericSitemap
from django.core.urlresolvers import reverse
from django.conf import settings
from bilanci.views import HierarchicalMenuMixin
from territori.models import Territorio


class BilancioBaseSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    destination_view = ''

    """Reverse static views for XML sitemap."""



    def generate_items(self):

        # Return list of url names for views to include in sitemap
        # ?year=2013&type=preventivo&values_type=real&cas_com_type=cassa
        territori = Territorio.objects.filter(territorio="C").values_list('slug',flat=True)
        years = range(settings.APP_START_DATE.year,settings.APP_END_DATE.year + 1)
        bilancio_types = ['preventivo', 'consuntivo']
        values_types = ['real','nominal']
        cas_com_types = ['cassa','competenza']
        section_types = ['entrate','spese']

        items = []
        for territorio in territori:
            for year in years:
                for bilancio_type in bilancio_types:
                    for value_type in values_types:
                        for cas_com_type in cas_com_types:

                            if self.destination_view == 'bilanci-overview':
                                items.append(
                                    {
                                        'slug': territorio,
                                        'year':year,
                                        'type':bilancio_type,
                                        'values_type':value_type,
                                        'cas_com_type': cas_com_type
                                    }
                                )
                            else:
                                for section in section_types:
                                    items.append(
                                    {
                                        'slug': territorio,
                                        'year':year,
                                        'type':bilancio_type,
                                        'values_type':value_type,
                                        'cas_com_type': cas_com_type,
                                        'section': section

                                    }
                                )

        return items


    def items(self):

        return self.generate_items()


class BilancioOverviewSitemap(BilancioBaseSitemap):

    destination_view = 'bilanci-overview'

    def location(self, item):
        query_string = "?year={0}&type={1}&values_type={2}&cas_com_type={3}".format(item['year'],item['type'], item['values_type'], item['cas_com_type'])
        return reverse('bilanci-overview', kwargs={'slug':item['slug']}, )+ query_string


class BilancioComposizioneSitemap(BilancioBaseSitemap):

    destination_view = 'bilanci-composizione'

    def location(self, item):
        query_string = "?year={0}&type={1}&values_type={2}&cas_com_type={3}".format(item['year'],item['type'], item['values_type'], item['cas_com_type'])
        return reverse(self.destination_view, kwargs={'slug':item['slug'], 'section': item['section']}, )+ query_string

class BilancioDettaglioSitemap(BilancioComposizioneSitemap):
    view_type = 'bilanci-dettaglio'



class ClassificheSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    destination_view = 'classifiche-list'

    """Reverse static views for XML sitemap."""



    def generate_items(self):

        years = range(settings.APP_START_DATE.year,settings.APP_END_DATE.year)
        hmm = HierarchicalMenuMixin()
        parameter_dict = hmm.get_parameter_list()

        items = []
        for year in years:
            for parameter_type, parameter_set in parameter_dict.iteritems():
                for parameter_list in parameter_set :
                    for parameter in parameter_list :

                        items.append(
                            {
                                'parameter_type': parameter_type.replace('_','-'),
                                'parameter_slug': parameter.slug,
                                'anno': year
                            }
                        )

        return items

    def location(self, item):

        return reverse(self.destination_view, kwargs=item)

    def items(self):

        return self.generate_items()



class ConfrontiSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    destination_view = 'confronti-entrate'

    """Reverse static views for XML sitemap."""


    def generate_items(self):

        # confronti between big cities
        territori = Territorio.objects.filter(territorio="C", cluster = '9').values_list('slug',flat=True)

        items = []
        for territorio_1 in territori:
            for territorio_2 in territori:
                if territorio_1 == territorio_2:
                    continue

                items.append(
                    {
                        'territorio_1_slug': territorio_1,
                        'territorio_2_slug': territorio_2,
                        'parameter_slug': settings.DEFAULT_VOCE_SLUG_CLASSIFICHE
                    }
                )

        return items

    def location(self, item):

        return reverse(self.destination_view, kwargs=item)

    def items(self):

        return self.generate_items()





sitemaps = {
    'overview': BilancioOverviewSitemap,
    'composizione': BilancioComposizioneSitemap,
    'dettaglio': BilancioDettaglioSitemap,
    'classifiche': ClassificheSitemap,
    'confronti': ConfrontiSitemap,
    }