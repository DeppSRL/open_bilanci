from django.contrib.sitemaps import Sitemap, GenericSitemap
from django.core.urlresolvers import reverse
from django.conf import settings
from territori.models import Territorio


class BilancioBaseSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    """Reverse static views for XML sitemap."""
    def items(self):
        # Return list of url names for views to include in sitemap
        # ?year=2013&type=preventivo&values_type=real&cas_com_type=cassa
        years = range(settings.APP_START_DATE.year,settings.APP_END_DATE.year + 1)
        bilancio_types = ['preventivo', 'consuntivo']
        values_types = ['real','nominal']
        cas_com_types = ['cassa','competenza']
        territori = Territorio.objects.filter(territorio="C").values('slug',)
        return


class BilancioOverviewSitemap(BilancioBaseSitemap):

    def location(self, item):
        return reverse('bilanci-overview', kwargs=item, )




sitemaps = {'views': BilancioOverviewSitemap, }