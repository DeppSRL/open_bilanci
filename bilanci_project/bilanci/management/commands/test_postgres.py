__author__ = 'stefano'
import logging
import multiprocessing
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from optparse import make_option
from pprint import pprint
from django.conf import settings
from django.core.management import BaseCommand
from bilanci.models import Voce, ValoreBilancio
from territori.models import Territorio

nodes_to_check=[
    'preventivo-spese-prestiti',
    'preventivo-spese-spese-correnti-funzioni',
    'preventivo-spese-spese-correnti-interventi',
    'preventivo-spese-spese-per-investimenti-funzioni',
    'preventivo-spese-spese-per-investimenti-interventi',
    'preventivo-spese-spese-somma-funzioni',
    'preventivo-entrate',
    'preventivo-entrate-imposte-e-tasse',
    'preventivo-entrate-contributi-pubblici',
    'preventivo-entrate-entrate-extratributarie',
    'preventivo-entrate-vendite-e-trasferimenti-di-capitali',
    'preventivo-entrate-prestiti',

    'consuntivo-spese-impegni-spese-correnti-interventi',
    'consuntivo-spese-impegni-spese-correnti-funzioni',
    'consuntivo-spese-impegni-spese-per-investimenti-funzioni',
	'consuntivo-spese-impegni-spese-per-investimenti-interventi',
    'consuntivo-spese-impegni-prestiti',
    'consuntivo-spese-impegni-spese-somma-funzioni',
    'consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-funzioni',
    'consuntivo-spese-pagamenti-in-conto-competenza-spese-correnti-interventi',
    'consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-funzioni',
    'consuntivo-spese-pagamenti-in-conto-competenza-spese-per-investimenti-interventi',
    'consuntivo-spese-pagamenti-in-conto-competenza-prestiti',
    'consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-funzioni',
    'consuntivo-spese-pagamenti-in-conto-residui-spese-correnti-interventi',
    'consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-funzioni',
    'consuntivo-spese-pagamenti-in-conto-residui-spese-per-investimenti-interventi',
    'consuntivo-spese-pagamenti-in-conto-residui-prestiti',
    'consuntivo-spese-cassa-spese-correnti-funzioni',
    'consuntivo-spese-cassa-spese-correnti-interventi',
    'consuntivo-spese-cassa-spese-per-investimenti-funzioni',
    'consuntivo-spese-cassa-spese-per-investimenti-interventi',
    'consuntivo-spese-cassa-prestiti',
    'consuntivo-spese-cassa-spese-somma-funzioni',

    'consuntivo-entrate-accertamenti',
    'consuntivo-entrate-accertamenti-imposte-e-tasse',
    'consuntivo-entrate-accertamenti-contributi-pubblici',
    'consuntivo-entrate-accertamenti-entrate-extratributarie',
    'consuntivo-entrate-accertamenti-prestiti',
    'consuntivo-entrate-accertamenti-entrate-per-conto-terzi',
    'consuntivo-entrate-accertamenti-vendite-e-trasferimenti-di-capitali',

    'consuntivo-entrate-riscossioni-in-conto-competenza',
    'consuntivo-entrate-riscossioni-in-conto-competenza-imposte-e-tasse',
    'consuntivo-entrate-riscossioni-in-conto-competenza-contributi-pubblici',
    'consuntivo-entrate-riscossioni-in-conto-competenza-entrate-extratributarie',
    'consuntivo-entrate-riscossioni-in-conto-competenza-prestiti',
    'consuntivo-entrate-riscossioni-in-conto-competenza-entrate-per-conto-terzi',
    'consuntivo-entrate-riscossioni-in-conto-competenza-vendite-e-trasferimenti-di-capitali',

    'consuntivo-entrate-riscossioni-in-conto-residui',
    'consuntivo-entrate-riscossioni-in-conto-residui-imposte-e-tasse',
    'consuntivo-entrate-riscossioni-in-conto-residui-contributi-pubblici',
    'consuntivo-entrate-riscossioni-in-conto-residui-entrate-extratributarie',
    'consuntivo-entrate-riscossioni-in-conto-residui-prestiti',
    'consuntivo-entrate-riscossioni-in-conto-residui-entrate-per-conto-terzi',
    'consuntivo-entrate-riscossioni-in-conto-residui-vendite-e-trasferimenti-di-capitali',

    'consuntivo-entrate-cassa',
    'consuntivo-entrate-cassa-imposte-e-tasse',
    'consuntivo-entrate-cassa-contributi-pubblici',
    'consuntivo-entrate-cassa-entrate-extratributarie',
    'consuntivo-entrate-cassa-prestiti',
    'consuntivo-entrate-cassa-entrate-per-conto-terzi',
    'consuntivo-entrate-cassa-vendite-e-trasferimenti-di-capitali',

]
years_to_check = range(settings.APP_START_YEAR, settings.APP_END_YEAR)

def check_city(city_slug):
    errors = []
    for voce_slug in nodes_to_check:
        for anno in years_to_check:
            totale_children=0
            totale_voce=0
            try:
                totale_voce = int(ValoreBilancio.objects.get(anno=anno, voce__slug=voce_slug, territorio__slug=city_slug).valore)
            except ObjectDoesNotExist:
                totale_voce=None
            try:
                totale_children = ValoreBilancio.objects.filter(anno=anno, voce__in=Voce.objects.get(slug=voce_slug).get_children(), territorio__slug=city_slug).aggregate(Sum('valore'))['valore__sum']
            except IndexError:
                totale_children=None

            if totale_children==None or totale_voce==None:
                diff = None
            else:
                diff = abs(totale_voce-totale_children)

            if diff > 1 or (totale_children==None and totale_voce==None):

                errors.append({'anno': anno, 'city_slug':city_slug, 'voce_slug':voce_slug, 'totale_voce':totale_voce, 'totale_children':totale_children, 'diff':diff})

    if len(errors) > 0:
        return errors
    return None


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the couchdb'),
        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server alias to connect to (staging | localhost). Defaults to staging.'),

    )

    help = 'Check that tree values in bilanci postgres DB are correct performing sums in some tree branches'
    dryrun = False
    logger = logging.getLogger('management')


    def handle(self, *args, **options):
        verbosity = options['verbosity']
        if verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        comuni = Territorio.objects.filter(territorio="C").order_by('slug')
        pool = multiprocessing.Pool()

        self.logger.info(u"Start calculation...")
        results = [pool.apply_async(check_city, (p,)) for p in settings.CAPOLUOGHI_PROVINCIA]
        for result in results:

            ret = result.get()
            if ret is None:
                continue
            for line in ret:

                if line['totale_voce'] is None and line['totale_children'] is None and  line['diff'] is None:
                    self.logger.warning("City:{}, year:{}, voce:{} is missing".format(line['city_slug'], line['anno'],line['voce_slug']))
                else:

                    self.logger.warning("City:{}, year:{}, voce:{}, value_voce:{}, value_children:{}, diff:{}".format(
                        line['city_slug'],
                        line['anno'],
                        line['voce_slug'],
                        line['totale_voce'],
                        line['totale_children'],
                        line['diff'],
                    ))
    
        return



