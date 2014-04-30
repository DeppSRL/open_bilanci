# encoding: utf-8
from django.core.exceptions import ObjectDoesNotExist
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
        key = (year, city, self.used_voci_slugs[slug_code])
        return float(data_dict[key])

    def get_indicator_obj(self):
        return Indicatore.objects.get(slug=self.slug)

    def get_formula_result(self, data_dict, city, year):
        raise Exception("Not implemented.")

    def compute(self, cities, years, logger=None):
        data_dict = self.get_data(cities, years)

        ret = OrderedDict([])
        for city in cities:
            ret[city] = OrderedDict([])
            for year in years:
                try:
                    ret[city][year] = self.get_formula_result(data_dict, city, year)
                    if logger:
                        logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                            city, year, ret[city][year]
                        ))
                except KeyError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valori mancanti.".format(
                            city, year
                        ))
                except ZeroDivisionError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valore nullo al denominatore.".format(
                            city, year
                        ))
        return ret

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
            try:
                city_obj = Territorio.objects.get(cod_finloc=city)
            except ObjectDoesNotExist:
                continue
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
                except KeyError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valori mancanti.".format(
                            city, year
                        ))



class AutonomiaFinanziariaIndicator(BaseIndicator):
    """
    (
     consuntivo-entrate-accertamenti-imposte-e-tasse +
     consuntivo-entrate-accertamenti-entrate-extratributarie
    )
    /
    (consuntivo-entrate-accertamenti-imposte-e-tasse +
     consuntivo-entrate-accertamenti-entrate-extratributarie +
     consuntivo-entrate-accertamenti-contributi-pubblici
    ) * 100
    """
    slug = 'autonomia-finanziaria'
    label = 'Autonomia finanziaria'
    used_voci_slugs = {
        'it': 'consuntivo-entrate-accertamenti-imposte-e-tasse',
        'ex': 'consuntivo-entrate-accertamenti-entrate-extratributarie',
        'pb': 'consuntivo-entrate-accertamenti-contributi-pubblici'
    }

    def get_formula_result(self, data_dict, city, year):
        it = self.get_val(data_dict, city,  year, 'it')
        ex = self.get_val(data_dict, city, year, 'ex')
        pb = self.get_val(data_dict, city, year, 'pb')
        return 100.0 / ( 1.0 + pb / ( it + ex ) )


class BontaPrevisioneSpesaCorrenteIndicator(BaseIndicator):
    """
    (preventivo-spese-spese-correnti - (consuntivo-spese-impegni-spese-correnti + consuntivo-spese-impegni-spese-per-investimenti) /
    preventivo-spese-spese-correnti * 100
    """
    slug = 'bonta-previsione-spesa-corrente'
    label = u'Bontà di previsione della spesa corrente'
    used_voci_slugs = {
        'psc': 'preventivo-spese-spese-correnti',
        'csc': 'consuntivo-spese-impegni-spese-correnti',
        'csi': 'consuntivo-spese-impegni-spese-per-investimenti',
    }

    def get_formula_result(self, data_dict, city, year):
        psc = self.get_val(data_dict, city, year, 'psc')
        csc = self.get_val(data_dict, city, year, 'csc')
        csi = self.get_val(data_dict, city, year, 'csi')
        return 100.0 * (1.0 - (csc+csi) / psc )



class QuotaSpesaPersonaleIndicator(BaseIndicator):
    """
    consuntivo-spese-cassa-spese-correnti-interventi-personale /
    consuntivo-spese-cassa-spese-correnti * 100
    """
    slug = 'quota-spesa-personale'
    label = u'Quota della spesa per il personale'
    used_voci_slugs = {
        'sp': 'consuntivo-spese-cassa-spese-correnti-interventi-personale',
        'sc': 'consuntivo-spese-cassa-spese-correnti',
    }

    def get_formula_result(self, data_dict, city, year):
        sp = self.get_val(data_dict, city, year, 'sp')
        sc = self.get_val(data_dict, city, year, 'sc')
        return 100.0 * sp / sc


class PropensioneInvestimentoIndicator(BaseIndicator):
    """
    media sul triennio di:
    consuntivo-spese-cassa-spese-per-investimenti /
    consuntivo-spese-cassa-spese-correnti * 100
    """
    slug = 'propensione-investimento-triennio'
    label = u"Propensione all’investimento - media sul triennio (t-2, t-1, t)"
    used_voci_slugs = {
        'si': 'consuntivo-spese-cassa-spese-per-investimenti',
        'sc': 'consuntivo-spese-cassa-spese-correnti',
    }

    def get_formula_result(self, data_dict, city, year):
        si = self.get_val(data_dict, city, year, 'si')
        sc = self.get_val(data_dict, city, year, 'sc')
        return 100.0 * si / sc

    # need to override the get_compute, to compute the 3-years average
    def compute(self, cities, years, logger=None):
        data_dict = self.get_data(cities, years)

        ret = OrderedDict([])
        for city in cities:
            ret[city] = OrderedDict([])
            for year in years:
                n_available_years = 0

                try:
                    t0 = self.get_formula_result(data_dict, city, year)
                    n_available_years += 1
                except KeyError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valori mancanti.".format(
                            city, year
                        ))
                    continue
                except ZeroDivisionError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valore nullo al denominatore.".format(
                            city, year
                        ))
                    continue
                try:
                    t1 = self.get_formula_result(data_dict, city, year-1)
                    n_available_years += 1
                except (KeyError, ZeroDivisionError):
                    t1 = 0

                try:
                    t2 = self.get_formula_result(data_dict, city, year-2)
                    n_available_years += 1
                except (KeyError, ZeroDivisionError):
                    t2 = 0

                ret[city][year] = (t0 + t1 + t2) / n_available_years
                if logger:
                    logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                        city, year, ret[city][year]
                    ))

        return ret


class VelocitaGestioneSpeseCorrentiIndicator(BaseIndicator):
    """
    (consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse + consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie) :
    (consuntivo-entrate-accertamenti-imposte-e-tasse + consuntivo-entrate-accertamenti-entrate-extratributarie) * 100
    """
    slug = 'velocita-riscossione-entrate-proprie'
    label = u"Velocità di riscossione delle entrate proprie"
    used_voci_slugs = {
        'ecit': 'consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse',
        'ecex': 'consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie',
        'eait': 'consuntivo-entrate-accertamenti-imposte-e-tasse',
        'eaex': 'consuntivo-entrate-accertamenti-entrate-extratributarie',
    }

    def get_formula_result(self, data_dict, city, year):
        ecit = self.get_val(data_dict, city, year, 'ecit')
        ecex = self.get_val(data_dict, city, year, 'ecex')
        eait = self.get_val(data_dict, city, year, 'eait')
        eaex = self.get_val(data_dict, city, year, 'eaex')
        return 100.0 * (ecit + ecex) / (eait + eaex)


class VelocitaRiscossioneEntrateProprieIndicator(BaseIndicator):
    """
    (consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti /
     consuntivo-spese-impegni-spese-correnti) * 100
    """
    slug = 'velocita-gestione-spese-correnti'
    label = u"Velocità di gestione delle spese correnti"
    used_voci_slugs = {
        'sp': 'consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti',
        'si': 'consuntivo-spese-impegni-spese-correnti',
    }

    def get_formula_result(self, data_dict, city, year):
        sp = self.get_val(data_dict, city, year, 'sp')
        si = self.get_val(data_dict, city, year, 'si')
        return 100.0 * sp  / si
