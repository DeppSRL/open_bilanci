import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from bilanci.tree_models import make_tree
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio
from bilanci.models import ValoreBilancio, Voce


__author__ = 'guglielmo'

class Command(BaseCommand):


    option_list = BaseCommand.option_list + (
        make_option('--year',
                    dest='year',
                    default='2004',
                    help='Year to consider. From 2002 to 2012.'),
        make_option('--city',
                    dest='city',
                    default='roma',
                    help='City code or slug.'),
    )

    help = 'Test the tree_models component'

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

        city_code = options['city']
        if not city_code:
            raise Exception("Missing city parameter")

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)
        city = mapper.get_city(city_code)

        year = options['year']

        preventivo_node = Voce.objects.get(slug='preventivo-spese-spese-per-investimenti-funzioni')
        t = Territorio.objects.get(cod_finloc=city)
        y = year
        valori_bilancio = ValoreBilancio.objects.filter(territorio=t, anno=y).\
            filter(voce__in=preventivo_node.get_descendants(include_self=True))
        valori_bilancio_dict = dict(
            (v['pk'], {'valore': v['valore'], 'valore_procapite': v['valore_procapite']})
            for v in valori_bilancio.values('pk', 'valore', 'valore_procapite')
        )
        bilanci_tree = make_tree(preventivo_node, valori_bilancio_dict)

        bilanci_tree.emit()
