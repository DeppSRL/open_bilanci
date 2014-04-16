# encoding: utf-8
from django.db.utils import IntegrityError
from bilanci.models import ValoreBilancio, ValoreIndicatore, Indicatore
from territori.models import Territorio
from collections import OrderedDict
from itertools import groupby

__author__ = 'guglielmo'

def _keygen(item):
    return (item['anno'], item['territorio__cod_finloc'], item['voce__slug'])


class BaseIndicator(object):
    slug = ''
    label = ''
    used_voci_slugs = {}

    def get_queryset(self, cities, years):
        qs = ValoreBilancio.objects.filter(
            voce__slug__in=self.used_voci_slugs.values(),
            anno__in=years
        )
        if len(cities) < Territorio.objects.filter(territorio=Territorio.TERRITORIO.C).count():
            qs = qs.filter(territorio__cod_finloc__in=cities)

        return qs.values(
            'voce__slug', 'anno', 'territorio__cod_finloc', 'valore', 'valore_procapite'
        ).order_by('anno', 'voce__slug')

    def get_data(self, cities, years):
        data_qs = self.get_queryset(cities, years)
        data_dict = dict( (k, [i['valore'] for i in list(v)][0] ) for k,v in groupby(data_qs, key=_keygen))
        return data_dict

    def get_data_procapite(self, cities, years):
        data_qs = self.get_queryset(cities, years)
        data_dict = dict( (k, [i['valore_procapite'] for i in list(v)][0] ) for k,v in groupby(data_qs, key=_keygen))
        return data_dict

    def get_val(self, data_dict, city, year, slug_code):
        return float(data_dict[(year, city, self.used_voci_slugs[slug_code])])

    def get_indicator_obj(self):
        return Indicatore.objects.get(slug=self.slug)

    def compute(self, cities, years, logger=None):
        raise Exception("To be implemented")

    def compute_and_commit(self, cities, years, logger=None, skip_existing=False):
        """
        Existing values are overwritten, by default
        """
        data = self.compute(cities, years)

        if not skip_existing:
            ValoreIndicatore.objects.filter(
                indicatore=self.get_indicator_obj(),
                territorio__cod_finloc__in=cities,
                anno__in=years
            ).delete()

        for city in cities:
            city_obj = Territorio.objects.get(cod_finloc=city)
            for year in years:
                try:
                    ValoreIndicatore.objects.create(
                        territorio=city_obj,
                        indicatore=self.get_indicator_obj(),
                        anno=year,
                        valore=data[city][year]
                    )
                    if logger:
                        logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                            city, year, data[city][year]
                        ))
                except IntegrityError:
                    pass


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
    label = 'Autonomia finanziaria'
    used_voci_slugs = {
        'it': 'consuntivo-entrate-cassa-imposte-e-tasse',
        'ex': 'consuntivo-entrate-cassa-entrate-extratributarie',
        'pb': 'consuntivo-entrate-cassa-contributi-pubblici'
    }

    def compute(self, cities, years, logger=None):
        data_dict = self.get_data(cities, years)

        ret = OrderedDict([])
        for city in cities:
            ret[city] = OrderedDict([])
            for year in years:
                it = self.get_val(data_dict, city,  year, 'it')
                ex = self.get_val(data_dict, city, year, 'ex')
                pb = self.get_val(data_dict, city, year, 'pb')
                ret[city][year] = 100.0 / ( 1.0 + pb / ( it + ex ) )
                if logger:
                    logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                        city, year, ret[city][year]
                    ))
        return ret


class BontaPrevisioneSpesaCorrenteIndicator(BaseIndicator):
    """
    (preventivo-spese-spese-correnti - consuntivo-spese-cassa-spese-correnti) /
    preventivo-spese-spese-correnti * 100
    """
    slug = 'bonta-previsione-spesa-corrente'
    label = u'Bontà di previsione della spesa corrente'
    used_voci_slugs = {
        'ps': 'preventivo-spese-spese-correnti',
        'cs': 'consuntivo-spese-cassa-spese-correnti',
    }

    def compute(self, cities, years, logger=None):
        data_dict = self.get_data(cities, years)

        ret = OrderedDict([])
        for city in cities:
            ret[city] = OrderedDict([])
            for year in years:
                ps = self.get_val(data_dict, city, year, 'ps')
                cs = self.get_val(data_dict, city, year, 'cs')
                ret[city][year] = 100.0 * (1.0 - cs / ps )
                if logger:
                    logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                        city, year, ret[city][year]
                    ))

        return ret


