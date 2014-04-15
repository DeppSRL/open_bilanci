from collections import OrderedDict
from itertools import groupby
from bilanci.models import ValoreBilancio, ValoreIndicatore

__author__ = 'guglielmo'

def _keygen(item):
    return (item['anno'], item['voce__slug'])


class BaseIndicator(object):
    slug = ''
    used_voci_slugs = {}

    def get_queryset(self, cities, years):
        return ValoreBilancio.objects.filter(
            voce__slug__in=self.used_voci_slugs.values(),
            anno__in=years,
            territorio__cod_finloc__in=cities
        ).values('voce__slug', 'anno', 'territorio', 'valore', 'valore_procapite').order_by('anno', 'voce__slug')

    def get_data(self, cities, years):
        data_qs = self.get_queryset(cities, years)
        data_dict = dict( (k, [i['valore'] for i in list(v)][0] ) for k,v in groupby(data_qs, key=_keygen))
        return data_dict

    def get_data_procapite(self, cities, years):
        data_qs = self.get_queryset(cities, years)
        data_dict = dict( (k, [i['valore_procapite'] for i in list(v)][0] ) for k,v in groupby(data_qs, key=_keygen))
        return data_dict

    def get_val(self, data_dict, year, slug_code):
        return float(data_dict[(year, self.used_voci_slugs[slug_code])])

    def compute(self, city, year):
        raise Exception("To be implemented")

    def compute_and_commit(self, city, year):
        """
        ASSUMPTION: The value does not exist.
        Must be deleted before
        """
        res = self.compute(city, year)

        ValoreIndicatore.objects.create(
            territorio=city,
            anno=year,
            valore=res
        )





class AutonomiaFinanziariaIndicator(BaseIndicator):
    """
    (
     consuntivo-entrate-cassa-imposte-e-tasse +
     consuntivo-entrate-cassa-entrate-extratributarie
    )
    /
    (consuntivo-entrate-cassa-imposte-e-tasse +
     consuntivo-entrate-cassa-entrate-extratributarie +
     consuntivo-entrate-cassa-contributi-pubblici
    ) * 100
    """
    slug = 'autonomia-finanziaria'
    used_voci_slugs = {
        'it': 'consuntivo-entrate-cassa-imposte-e-tasse',
        'ex': 'consuntivo-entrate-cassa-entrate-extratributarie',
        'pb': 'consuntivo-entrate-cassa-contributi-pubblici'
    }

    def compute(self, cities, years):

        data_dict = self.get_data(cities, years)

        ret = OrderedDict([])
        for year in years:
            it = self.get_val(data_dict, year, 'it')
            ex = self.get_val(data_dict, year, 'ex')
            pb = self.get_val(data_dict, year, 'pb')

            ret[year] = 100.0 / ( 1.0 + pb / ( it + ex ) )
        return ret




class BontaPrevisioneSpesaCorrenteIndicator(BaseIndicator):
    """
    (preventivo-spese-spese-correnti - consuntivo-spese-cassa-spese-correnti) /
    preventivo-spese-spese-correnti * 100
    """
    slug = 'bonta-previsione-spesa-corrente'
    used_voci_slugs = {
        'ps': 'preventivo-spese-spese-correnti',
        'cs': 'consuntivo-spese-cassa-spese-correnti',
    }


    def compute(self, cities, years):

        data_dict = self.get_data(cities, years)

        ret = OrderedDict([])
        for year in years:
            ps = self.get_val(data_dict, year, 'ps')
            cs = self.get_val(data_dict, year, 'cs')
            ret[year] = 100.0 * (1.0 - cs / ps )

        return ret


