# encoding: utf-8
import math
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from bilanci.models import ValoreBilancio, ValoreIndicatore, Indicatore
from territori.models import Territorio, Contesto
from collections import OrderedDict
from itertools import groupby

__author__ = 'guglielmo'

def _keygen(item):
    return (item['anno'], item['territorio__slug'], item['voce__slug'])

def _abitanti_keygen(item):
    return (item['anno'], item['territorio__cod_finloc'],'bil_popolazione_residente')


class BaseIndicator(object):
    slug = ''
    label = ''
    create_counter_limit = 5000
    used_voci_slugs = {}

    def get_queryset(self, cities, years):
        qs = ValoreBilancio.objects.filter(
            voce__slug__in=self.used_voci_slugs.values(),
            anno__in=years
        )
        if len(cities) < Territorio.objects.filter(territorio=Territorio.TERRITORIO.C).count():
            qs = qs.filter(territorio__in=cities)

        return qs.values(
            'voce__slug', 'anno', 'territorio__slug', 'valore', 'valore_procapite'
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

        data = OrderedDict([])
        for city in cities:
            data[city.slug] = OrderedDict([])
            for year in years:
                try:
                    data[city.slug][year] = self.get_formula_result(data_dict, city.slug, year)
                    if logger:
                        logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                            city.slug, year, data[city.slug][year]
                        ))
                except KeyError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valori mancanti.".format(
                            city.slug, year
                        ))
                except ZeroDivisionError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valore nullo al denominatore.".format(
                            city.slug, year
                        ))
        return data

    def compute_and_commit(self, cities, years, logger=None, skip_existing=False):
        """
        Existing values are overwritten, by default
        """
        data = self.compute(cities, years, logger=logger)

        if not skip_existing:
            from pprint import pprint
            ValoreIndicatore.objects.filter(
                indicatore=self.get_indicator_obj(),
                territorio__in=cities,
                anno__in=years
            ).delete()


        for city in cities:
            for year in years:
                try:
                    ValoreIndicatore.objects.create(
                        territorio=city,
                        indicatore=self.get_indicator_obj(),
                        anno=year,
                        valore=data[city.slug][year]
                    )
                    if logger:
                        logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                            city.slug, year, data[city.slug][year]
                        ))
                except IntegrityError:
                    pass
                except KeyError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Cannot compute indicator".format(
                            city.slug, year
                        ))



class PerCapitaIndicatorType(BaseIndicator):

    def compute(self, cities, years, logger=None):
        data_dict = self.get_data_procapite(cities, years)

        ret = OrderedDict([])
        for city in cities:
            ret[city.slug] = OrderedDict([])
            for year in years:
                try:
                    ret[city.slug][year] = self.get_formula_result(data_dict, city.slug, year)
                    if logger:
                        logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                            city, year, ret[city.slug][year]
                        ))
                except KeyError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valori mancanti.".format(
                            city.slug, year
                        ))
                except ZeroDivisionError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valore nullo al denominatore.".format(
                            city.slug, year
                        ))
        return ret



class ThreeYearsMeanIndicatorType(BaseIndicator):

    slug = ''

    # need to override the get_compute, to compute the 3-years average
    def compute(self, cities, years, logger=None):
        data_dict = self.get_data(cities, years)

        ret = OrderedDict([])
        for city in cities:
            ret[city.slug] = OrderedDict([])
            for year in years:
                n_available_years = 0

                try:
                    t0 = self.get_formula_result(data_dict, city.slug, year)
                    n_available_years += 1
                except KeyError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valori mancanti.".format(
                            city.slug, year
                        ))
                    continue
                except ZeroDivisionError:
                    if logger:
                        logger.warning("City: {0}, Year: {1}. Valore nullo al denominatore.".format(
                            city.slug, year
                        ))
                    continue
                try:
                    t1 = self.get_formula_result(data_dict, city.slug, year-1)
                    n_available_years += 1
                except (KeyError, ZeroDivisionError):
                    t1 = 0

                try:
                    t2 = self.get_formula_result(data_dict, city.slug, year-2)
                    n_available_years += 1
                except (KeyError, ZeroDivisionError):
                    t2 = 0

                ret[city.slug][year] = (t0 + t1 + t2) / n_available_years
                if logger:
                    logger.debug("City: {0}, Year: {1}, valore: {2}".format(
                        city.slug, year, ret[city.slug][year]
                    ))

        return ret


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
    published = True
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
    abs(psc - csc)/(psc + csc)
    """

    slug = 'bonta-previsione-spesa-corrente'
    label = u'Bontà di previsione della spesa corrente'
    published = False
    used_voci_slugs = {
        'psc': 'preventivo-spese-spese-correnti',
        'csc': 'consuntivo-spese-impegni-spese-correnti',
    }

    def get_formula_result(self, data_dict, city, year):
        psc = self.get_val(data_dict, city, year, 'psc')
        csc = self.get_val(data_dict, city, year, 'csc')

        return (1.0-(abs(psc - csc)/(psc + csc)))*100.0



class SpesaPerIlPersonaleIndicator(BaseIndicator):
    """
    consuntivo-spese-cassa-spese-correnti-interventi-personale /
    consuntivo-spese-cassa-spese-correnti * 100
    """
    slug = 'spesa-per-il-personale'
    label = u'Spesa per il personale'
    published = True
    used_voci_slugs = {
        'sp': 'consuntivo-spese-cassa-spese-correnti-interventi-personale',
        'sc': 'consuntivo-spese-cassa-spese-correnti',
    }

    def get_formula_result(self, data_dict, city, year):
        sp = self.get_val(data_dict, city, year, 'sp')
        sc = self.get_val(data_dict, city, year, 'sc')
        return 100.0 * sp / sc


class PropensioneInvestimentoIndicator(ThreeYearsMeanIndicatorType):
    """
    media sul triennio di:
    consuntivo-spese-cassa-spese-per-investimenti /
    consuntivo-spese-cassa-spese-correnti * 100
    """
    slug = 'investimenti'
    label = u"Investimenti"
    published = True
    used_voci_slugs = {
        'si': 'consuntivo-spese-cassa-spese-per-investimenti',
        'sc': 'consuntivo-spese-cassa-spese-correnti',
    }

    def get_formula_result(self, data_dict, city, year):
        si = self.get_val(data_dict, city, year, 'si')
        sc = self.get_val(data_dict, city, year, 'sc')
        return 100.0 * si / sc



class VelocitaRiscossioneEntrateProprieIndicator(BaseIndicator):
    """
    (consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse + consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie) :
    (consuntivo-entrate-accertamenti-imposte-e-tasse + consuntivo-entrate-accertamenti-entrate-extratributarie) * 100
    """
    slug = 'velocita-riscossione-entrate-proprie'
    label = u"Velocità di riscossione delle entrate proprie"
    published = False
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


class VelocitaGestioneSpeseCorrentiIndicator(BaseIndicator):
    """
    (consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti /
     consuntivo-spese-impegni-spese-correnti) * 100
    """
    slug = 'velocita-gestione-spese-correnti'
    label = u"Velocità di gestione delle spese correnti"
    published = False
    used_voci_slugs = {
        'sp': 'consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti',
        'si': 'consuntivo-spese-impegni-spese-correnti',
    }

    def get_formula_result(self, data_dict, city, year):
        sp = self.get_val(data_dict, city, year, 'sp')
        si = self.get_val(data_dict, city, year, 'si')
        return 100.0 * sp  / si


class GradoRigiditaStrutturaleSpesaIndicator(BaseIndicator):
    """
    ((consuntivo-spese-cassa-spese-correnti-interventi-personale +
    consuntivo-spese-impegni-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi +
    consuntivo-spese-cassa-prestiti-quota-capitale-di-mutui-e-prestiti) /
    (consuntivo-entrate-cassa-imposte-e-tasse + consuntivo-entrate-cassa-entrate-extratributarie +
    consuntivo-entrate-cassa-contributi-pubblici) * 100

    """

    slug = 'rigidita-della-spesa'
    label = u'Rigidità della spesa'
    published = True
    used_voci_slugs = {
        'scip': 'consuntivo-spese-cassa-spese-correnti-interventi-personale',
        'csisciipeofd': 'consuntivo-spese-impegni-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi',
        'cscpqcdmep': 'consuntivo-spese-cassa-prestiti-quota-capitale-di-mutui-e-prestiti',
        'ceciet': 'consuntivo-entrate-cassa-imposte-e-tasse',
        'cecee': 'consuntivo-entrate-cassa-entrate-extratributarie',
        'ceccp': 'consuntivo-entrate-cassa-contributi-pubblici',

    }

    def get_formula_result(self, data_dict, city, year):
        scip = self.get_val(data_dict, city, year, 'scip')
        csisciipeofd = self.get_val(data_dict, city, year, 'csisciipeofd')
        cscpqcdmep = self.get_val(data_dict, city, year, 'cscpqcdmep')
        ceciet = self.get_val(data_dict, city, year, 'ceciet')
        cecee = self.get_val(data_dict, city, year, 'cecee')
        ceccp = self.get_val(data_dict, city, year, 'ceccp')


        return ((scip+csisciipeofd+cscpqcdmep)/(ceciet+cecee+ceccp))*100.0


class EquilibrioParteCorrenteIndicator(BaseIndicator):

    """
    [(consuntivo-entrate-cassa-imposte-e-tasse + consuntivo-entrate-cassa-contributi-pubblici + consuntivo-entrate-cassa-entrate-extratributarie) /
    consuntivo-spese-cassa-spese-correnti] * 100
    """

    slug = 'equilibrio-parte-corrente'
    label = u'Equilibrio della parte corrente'
    published = True
    used_voci_slugs = {
        'ecit': 'consuntivo-entrate-cassa-imposte-e-tasse',
        'eccp':  'consuntivo-entrate-cassa-contributi-pubblici',
        'ecee': 'consuntivo-entrate-cassa-entrate-extratributarie',
        'scsc': 'consuntivo-spese-cassa-spese-correnti',
    }


    def get_formula_result(self, data_dict, city, year):

        ecit = self.get_val(data_dict, city, year, 'ecit')
        eccp = self.get_val(data_dict, city, year, 'eccp')
        ecee = self.get_val(data_dict, city, year, 'ecee')
        scsc = self.get_val(data_dict, city, year, 'scsc')

        return ((ecit + eccp + ecee)/scsc)*100.0



class SaldoCorrenteLordoIndicator(BaseIndicator):

    """

    {[(consuntivo-entrate-accertamenti-imposte-e-tasse +
    consuntivo-entrate-accertamenti-contributi-pubblici +
    consuntivo-entrate-accertamenti-entrate-extratributarie) –
    consuntivo-spese-impegni] /

    (consuntivo-entrate-accertamenti-imposte-e-tasse +
    consuntivo-entrate-accertamenti-contributi-pubblici +
    consuntivo-entrate-accertamenti-entrate-extratributarie)}*100


    """

    slug = 'saldo-corrente-lordo'
    label = u'Saldo corrente lordo'
    published = False
    used_voci_slugs = {
      'ceait' : 'consuntivo-entrate-accertamenti-imposte-e-tasse',
      'ceacp' : 'consuntivo-entrate-accertamenti-contributi-pubblici',
      'ceaet' : 'consuntivo-entrate-accertamenti-entrate-extratributarie',
      'csi' : 'consuntivo-spese-impegni',
    }


    def get_formula_result(self, data_dict, city, year):

        ceait = self.get_val(data_dict, city, year, 'ceait')
        ceacp = self.get_val(data_dict, city, year, 'ceacp')
        ceaet = self.get_val(data_dict, city, year, 'ceaet')
        csi = self.get_val(data_dict, city, year, 'csi')

        somma_entrate =  ceait + ceacp + ceaet


        return ((somma_entrate - csi)/somma_entrate ) * 100.0



class SaldoNettoDaFinanziarieIndicator(BaseIndicator):

    """

    {[
    (preventivo-entrate-avanzo-di-amministrazione +
    preventivo-entrate-imposte-e-tasse +
    preventivo-entrate-contributi-pubblici +
    preventivo-entrate-entrate-extratributarie +
    preventivo-entrate-vendite-e-trasferimenti-di-capitali) -

    (preventivo-spese-disavanzo-di-amministrazione +
    preventivo-spese-spese-correnti +
    preventivo-spese-spese-per-investimenti)
    ]
    /
    (preventivo-entrate-avanzo-di-amministrazione +
    preventivo-entrate-imposte-e-tasse +
    preventivo-entrate-contributi-pubblici +
    preventivo-entrate-entrate-extratributarie +
    preventivo-entrate-vendite-e-trasferimenti-di-capitali)
    }*100


    """

    slug = 'saldo-netto-da-finanziarie'
    label = u'Saldo netto da finanziarie'
    published = False
    used_voci_slugs = {
        'peaa' : 'preventivo-entrate-avanzo-di-amministrazione',
        'peit' : 'preventivo-entrate-imposte-e-tasse',
        'pecp' : 'preventivo-entrate-contributi-pubblici',
        'peee' : 'preventivo-entrate-entrate-extratributarie',
        'pevtc' : 'preventivo-entrate-vendite-e-trasferimenti-di-capitali',
        'psda' : 'preventivo-spese-disavanzo-di-amministrazione',
        'pssc' : 'preventivo-spese-spese-correnti',
        'psspi' : 'preventivo-spese-spese-per-investimenti',
    }


    def get_formula_result(self, data_dict, city, year):

        peaa = self.get_val(data_dict, city, year, 'peaa')
        peit = self.get_val(data_dict, city, year, 'peit')
        pecp = self.get_val(data_dict, city, year, 'pecp')
        peee = self.get_val(data_dict, city, year, 'peee')
        pevtc = self.get_val(data_dict, city, year, 'pevtc')
        psda = self.get_val(data_dict, city, year, 'psda')
        pssc = self.get_val(data_dict, city, year, 'pssc')
        psspi = self.get_val(data_dict, city, year, 'psspi')

        somma_entrate = peaa + peit + pecp + peee + pevtc
        somma_spese = psda + pssc + psspi

        return ((somma_entrate - somma_spese)/ somma_entrate) * 100.0



class AvanzoNettoAmministrazioneIndicator(BaseIndicator):

    """
    (Consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-risultato-di-amministrazione / consuntivo-spese-cassa )*100

    """

    slug = 'avanzo-netto-amministrazione'
    label = u'Avanzo netto Amministrazione'
    published = False
    used_voci_slugs = {
        'trda' : 'consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-risultato-di-amministrazione',
        'csc' : 'consuntivo-spese-cassa',
    }


    def get_formula_result(self, data_dict, city, year):

        trda = self.get_val(data_dict, city, year, 'trda')
        csc = self.get_val(data_dict, city, year, 'csc')

        return (trda / csc) * 100.0



class SpesaPerInteresseIndicator(BaseIndicator):

    """
    (consuntivo-spese-impegni-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi / consuntivo-spese-impegni )*100

    """

    slug = 'spesa-per-interesse'
    label = u'Spesa per interesse'
    published = False
    used_voci_slugs = {
        'sciipeofd' : 'consuntivo-spese-impegni-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi',
        'csi' : 'consuntivo-spese-impegni',
    }


    def get_formula_result(self, data_dict, city, year):

        sciipeofd = self.get_val(data_dict, city, year, 'sciipeofd')
        csi = self.get_val(data_dict, city, year, 'csi')

        return (sciipeofd / csi) * 100.0


class IndebitamentoNettoGarantitoIndicator(BaseIndicator):

    """

    [(consuntivo-entrate-accertamenti – consuntivo-spese-impegni)/ consuntivo-spese-impegni ]*100


    """

    slug = 'indebitamento-netto-garantito'
    label = u'Indebitamento netto e garantito'
    published = False
    used_voci_slugs = {
        'cea' : 'consuntivo-entrate-accertamenti',
        'csi' : 'consuntivo-spese-impegni',
    }


    def get_formula_result(self, data_dict, city, year):

        cea = self.get_val(data_dict, city, year, 'cea')
        csi = self.get_val(data_dict, city, year, 'csi')

        return ((cea-csi) / csi) *100.0


class IndebitamentoDirettoBreveTermineIndicator(BaseIndicator):

    """
    (Consuntivo-spese-impegni-prestiti-finanziamenti-a-breve-termine / consuntivo-spese-impegni)*100


    """

    slug = 'indebitamento-diretto-breve-termine'
    label = u'Indebitamento diretto a breve termine'
    published = False
    used_voci_slugs = {
        'csipfbt' : 'consuntivo-spese-impegni-prestiti-finanziamenti-a-breve-termine',
        'csi' : 'consuntivo-spese-impegni',
    }


    def get_formula_result(self, data_dict, city, year):

        csipfbt = self.get_val(data_dict, city, year, 'csipfbt')
        csi = self.get_val(data_dict, city, year, 'csi')

        return (csipfbt / csi ) *100.0



class VariazioneTriennaleIndebitamentoNettoGarantitoIndicator(ThreeYearsMeanIndicatorType):
    """
         [(  {[(consuntivo-entrate-accertamenti - consuntivo-spese-impegni)t1 /
            (consuntivo-entrate-accertamenti-imposte-e-tasse +
            consuntivo-entrate-accertamenti-contributi-pubblici +
            consuntivo-entrate-accertamenti-entrate-extratributarie) (t=3)]
            /
            [(consuntivo-entrate-accertamenti - consuntivo-spese-impegni) /
            (consuntivo-entrate-accertamenti-imposte-e-tasse +
            consuntivo-entrate-accertamenti-contributi-pubblici +
            consuntivo-entrate-accertamenti-entrate-extratributarie) (t=1)
            ]} ^ 1/3
        ) -1 ] * 100

    """
    slug = 'variazione-triennale-indebitamento-netto-garantito'
    label = u"Variazione triennale dell'indebitamento netto e garantito sulle entrate correnti"
    published = False
    used_voci_slugs = {
        'cea' : 'consuntivo-entrate-accertamenti',
        'csi' : 'consuntivo-spese-impegni',
        'ceait' : 'consuntivo-entrate-accertamenti-imposte-e-tasse',
        'ceacp' : 'consuntivo-entrate-accertamenti-contributi-pubblici',
        'ceaee' : 'consuntivo-entrate-accertamenti-entrate-extratributarie',
    }

    def get_formula_result(self, data_dict, city, year):
        cea = self.get_val(data_dict, city, year, 'cea')
        csi = self.get_val(data_dict, city, year, 'csi')
        ceait = self.get_val(data_dict, city, year, 'ceait')
        ceacp = self.get_val(data_dict, city, year, 'ceacp')
        ceaee = self.get_val(data_dict, city, year, 'ceaee')

        ing = cea-csi
        ec = ceait + ceacp + ceaee


        return ing / ec



##
# Release 2 Evabeta
##


class RisultatoAmministrazioneIndicator(BaseIndicator):

    """
        Saldo di cassa + residui attivi - residui passivi

    """

    slug = 'risultato-amministrazione'
    label = u"Risultato d'amministrazione"
    published = False
    used_voci_slugs = {
        'crra' : 'consuntivo-riassuntivo-gestione-finanziaria-gestione-totale-risultato-di-amministrazione',
    }


    def get_formula_result(self, data_dict, city, year):

        crra = self.get_val(data_dict, city, year, 'crra')

        return crra




class DebitoComplessivoIndicator(BaseIndicator):

    """
        [
            (consuntivo-riassuntivo-debito-consistenza-finale +

            (consuntivo-riassuntivo-debiti-fuori-bilancio -
            consuntivo-riassuntivo-debiti-fuori-bilancio-sentenze-esecutive)
            ] /
            (consuntivo-entrate-cassa-imposte-e-tasse +
            consuntivo-entrate-cassa-contributi-pubblici +
            consuntivo-entrate-cassa-entrate-extratributarie) * 100

    """

    slug = 'debito-complessivo-entrate-correnti'
    label = u"Debito complessivo"
    published = True
    used_voci_slugs = {
        'crdcf' : 'consuntivo-riassuntivo-debito-consistenza-finale',
        'crdfb' : 'consuntivo-riassuntivo-debiti-fuori-bilancio',
        'crdfbse' : 'consuntivo-riassuntivo-debiti-fuori-bilancio-sentenze-esecutive',
        'ceciet' : 'consuntivo-entrate-cassa-imposte-e-tasse',
        'ceccp' : 'consuntivo-entrate-cassa-contributi-pubblici',
        'cecee' : 'consuntivo-entrate-cassa-entrate-extratributarie',
    }


    def get_formula_result(self, data_dict, city, year):

        crdcf = self.get_val(data_dict, city, year, 'crdcf')
        crdfb = self.get_val(data_dict, city, year, 'crdfb')
        crdfbse = self.get_val(data_dict, city, year, 'crdfbse')
        ceciet = self.get_val(data_dict, city, year, 'ceciet')
        ceccp = self.get_val(data_dict, city, year, 'ceccp')
        cecee = self.get_val(data_dict, city, year, 'cecee')

        return (crdcf+(crdfb-crdfbse))/(ceciet+ceccp+cecee)*100.0



class CostoIndebitamentoIndicator(BaseIndicator):

    """
        (consuntivo-spese-cassa-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi /
        consuntivo-riassuntivo-debito-consistenza-iniziale) * 100


    """

    slug = 'costo-indebitamento'
    label = u"Costo dell'indebitamento"
    published = True
    used_voci_slugs = {
        'cscsciipofd' : 'consuntivo-spese-cassa-spese-correnti-interventi-interessi-passivi-e-oneri-finanziari-diversi',
        'crdci' : 'consuntivo-riassuntivo-debito-consistenza-iniziale',
    }


    def get_formula_result(self, data_dict, city, year):

        cscsciipofd = self.get_val(data_dict, city, year, 'cscsciipofd')
        crdci = self.get_val(data_dict, city, year, 'crdci')

        return (cscsciipofd/crdci)*100.0



class AutonomiaImpositivaIndicator(BaseIndicator):

    """
       (consuntivo-entrate-accertamenti-imposte-e-tasse) /
        (consuntivo-entrate-accertamenti-imposte-e-tasse +
        consuntivo-entrate-accertamenti-contributi-pubblici +
        consuntivo-entrate-accertamenti-entrate-extratributarie) * 100

    """

    slug = 'autonomia-impositiva'
    label = u"Autonomia impositiva"
    published = False
    used_voci_slugs = {
        'ceaiet' : 'consuntivo-entrate-accertamenti-imposte-e-tasse',
        'ceacp' : 'consuntivo-entrate-accertamenti-contributi-pubblici',
        'ceaee' : 'consuntivo-entrate-accertamenti-entrate-extratributarie',
    }


    def get_formula_result(self, data_dict, city, year):

        ceaiet = self.get_val(data_dict, city, year, 'ceaiet')
        ceacp = self.get_val(data_dict, city, year, 'ceacp')
        ceaee = self.get_val(data_dict, city, year, 'ceaee')

        return (ceaiet/(ceaiet + ceacp + ceaee))*100.0


class GradoDipendenzaErarialeIndicator(BaseIndicator):

    """
       (consuntivo-entrate-accertamenti-contributi-pubblici-contributi-dallo-stato)
       /
       (consuntivo-entrate-accertamenti-imposte-e-tasse +
       consuntivo-entrate-accertamenti-contributi-pubblici +
       consuntivo-entrate-accertamenti-entrate-extratributarie) * 100


    """

    slug = 'dipendenza-dallo-stato'
    label = u"Dipendenza dallo Stato"
    published = True
    used_voci_slugs = {
        'ceacpcds' : 'consuntivo-entrate-accertamenti-contributi-pubblici-contributi-dallo-stato',
        'ceaiet' : 'consuntivo-entrate-accertamenti-imposte-e-tasse',
        'ceacp' : 'consuntivo-entrate-accertamenti-contributi-pubblici',
        'ceaee' : 'consuntivo-entrate-accertamenti-entrate-extratributarie',
    }


    def get_formula_result(self, data_dict, city, year):

        ceacpcds = self.get_val(data_dict, city, year, 'ceacpcds')
        ceaiet = self.get_val(data_dict, city, year, 'ceaiet')
        ceacp = self.get_val(data_dict, city, year, 'ceacp')
        ceaee = self.get_val(data_dict, city, year, 'ceaee')

        return (ceacpcds/(ceaiet + ceacp + ceaee))*100.0


class CapacitaSpesaComplessivaIndicator(BaseIndicator):

    """
     (consuntivo-spese-cassa / consuntivo-spese-impegni) * 100

    """

    slug = 'capacita-spesa-complessiva'
    label = u"Capacità di spesa complessiva"
    published = False
    used_voci_slugs = {
        'csc' : 'consuntivo-spese-cassa',
        'csi' : 'consuntivo-spese-impegni',
    }


    def get_formula_result(self, data_dict, city, year):

        csc = self.get_val(data_dict, city, year, 'csc')
        csi = self.get_val(data_dict, city, year, 'csi')

        return (csc/csi)*100.0



class AffidabilitaResiduiAttiviIndicator(ThreeYearsMeanIndicatorType):

    """
     consuntivo-riassuntivo-residui-attivi-iniziali /
     consuntivo-riassuntivo-residui-attivi-riscossi * 100

    """

    slug = 'affidabilita-residui-attivi'
    label = u"Affidabilità dei residui attivi"
    published = True
    used_voci_slugs = {
        'rai' : 'consuntivo-riassuntivo-residui-attivi-iniziali',
        'rar' : 'consuntivo-riassuntivo-residui-attivi-riscossi',
    }


    def get_formula_result(self, data_dict, city, year):

        rai = self.get_val(data_dict, city, year, 'rai')
        rar = self.get_val(data_dict, city, year, 'rar')

        return (rar/rai)*100.0



class SmaltimentoResiduiPassiviIndicator(ThreeYearsMeanIndicatorType):

    """
        consuntivo-riassuntivo-residui-passivi-iniziali
        /
        consuntivo-riassuntivo-residui-passivi-pagati  * 100

    """

    slug = 'smaltimento-residui-passivi'
    label = u"Smaltimento dei residui passivi"
    published = True
    used_voci_slugs = {
        'rpi' : 'consuntivo-riassuntivo-residui-passivi-iniziali',
        'rpr' : 'consuntivo-riassuntivo-residui-passivi-pagati',
    }


    def get_formula_result(self, data_dict, city, year):

        rpi = self.get_val(data_dict, city, year, 'rpi')
        rpr = self.get_val(data_dict, city, year, 'rpr')

        return (rpr/rpi)*100.0



class SpesaPersonalePerAbitanteIndicator(PerCapitaIndicatorType):

    """
        (consuntivo-spese-cassa-spese-correnti-interventi-personale / Popolazione al 1° gennaio)

    """

    slug = 'spesa-personale-per-abitante'
    label = u"Spesa per il personale per abitante"
    published = False
    used_voci_slugs = {
        'scip' : 'consuntivo-spese-cassa-spese-correnti-interventi-personale',
    }


    def get_formula_result(self, data_dict, city, year):

        scip = self.get_val(data_dict, city, year, 'scip')

        return scip



class PressioneTributariaePerAbitanteIndicator(PerCapitaIndicatorType):

    """
        consuntivo-entrate-accertamenti-imposte-e-tasse  / Popolazione al 1° gennaio

    """

    slug = 'pressione-tributaria-per-abitante'
    label = u"Pressione tributaria per abitante"
    published = False
    used_voci_slugs = {
        'ceait' : 'consuntivo-entrate-accertamenti-imposte-e-tasse',
    }


    def get_formula_result(self, data_dict, city, year):

        ceait = self.get_val(data_dict, city, year, 'ceait')

        return ceait


class InvestimentiPerAbitanteIndicator(PerCapitaIndicatorType):

    """
        (consuntivo-spese-cassa-spese-per-investimenti -
        consuntivo-spese-cassa-spese-per-investimenti-interventi-concessioni-di-crediti-e-anticipazioni) /
        Popolazione al 1° gennaio


    """

    slug = 'investimenti-per-abitante'
    label = u"Investimenti per abitante"
    published = False
    used_voci_slugs = {
        'cscsi' : 'consuntivo-spese-cassa-spese-per-investimenti',
        'cscsiicca' : 'consuntivo-spese-cassa-spese-per-investimenti-interventi-concessioni-di-crediti-e-anticipazioni',
    }


    def get_formula_result(self, data_dict, city, year):

        cscsi = self.get_val(data_dict, city, year, 'cscsi')
        cscsiicca = self.get_val(data_dict, city, year, 'cscsiicca')

        return cscsi-cscsiicca


class TrasferimentiCorrentiDalloStatoPerAbitanteIndicator(PerCapitaIndicatorType):

    """
       consuntivo-entrate-accertamenti-contributi-pubblici-contributi-dallo-stato / popolazione al 1° gennaio

    """

    slug = 'trasferimenti-correnti-dallo-stato-per-abitante'
    label = u"Trasferimenti correnti dallo Stato per abitante"
    published = False
    used_voci_slugs = {
        'cea' : 'consuntivo-entrate-accertamenti-contributi-pubblici-contributi-dallo-stato',
    }


    def get_formula_result(self, data_dict, city, year):

        cea = self.get_val(data_dict, city, year, 'cea')

        return cea



class PressioneFinanziariaPerAbitanteIndicator(PerCapitaIndicatorType):

    """
       (consuntivo-entrate-accertamenti-imposte-e-tasse + consuntivo-entrate-accertamenti-entrate-extratributarie) / popolazione al 1° gennaio

    """

    slug = 'pressione-finanziaria-per-abitante'
    label = u"Pressione finanziaria per abitante"
    published = False
    used_voci_slugs = {
        'ceatit' : 'consuntivo-entrate-accertamenti-imposte-e-tasse',
        'ceaee' : 'consuntivo-entrate-accertamenti-entrate-extratributarie',
    }


    def get_formula_result(self, data_dict, city, year):

        ceatit = self.get_val(data_dict, city, year, 'ceatit')
        ceaee = self.get_val(data_dict, city, year, 'ceaee')

        return ceatit + ceaee


