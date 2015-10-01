# coding=utf-8
import csvkit
import logging
from optparse import make_option
from django.core.management import BaseCommand
from bilanci.models import Indicatore, ValoreIndicatore, Voce, ValoreBilancio

##
# compute specific indicatore and budget voices values for
# all cities, in given years
##


class Command(BaseCommand):

    default_indicators = \
        'autonomia-finanziaria,rigidita-della-spesa,' +\
        'spesa-personale-per-abitante,affidabilita-residui-attivi,' +\
        'investimenti-per-abitante,debito-complessivo-entrate-correnti'

    default_voices = \
        'consuntivo-spese-cassa-spese-somma-funzioni-amministrazione,' +\
        'consuntivo-spese-cassa-spese-somma-funzioni-sociale-asili-nido,' +\
        'consuntivo-entrate-cassa-imposte-e-tasse,' +\
        'consuntivo-entrate-cassa-entrate-extratributarie-' +\
          'utili-delle-aziende-partecipate'

    option_list = BaseCommand.option_list + (
        make_option('--site-url',
                    dest='site_url',
                    default='http://www.openbilanci.it',
                    help='The site homepage URL, ' +
                         'to test in development or staging environments'),
        make_option('--year',
                    dest='year',
                    default='',
                    help='Year to fetch. From 2002.'),
        make_option('--indicators',
                    dest='indicators',
                    default=default_indicators,
                    help='Indicators slugs. Use comma to separate values: ' +
                         'autonomia-finanziaria,affidabilita-residui,...'),
        make_option('--voices',
                    dest='voices',
                    default=default_voices,
                    help='Budget value voices\' slugs. ' +
                         'Use comma to separate values, may use none'),
    )

    help = """Compute indicators and budget voices values for
    all cities and spits them out as CSV in the current directory.
    Used to build data to be uploaded to CartoDB."""

    logger = logging.getLogger('management')
    comuni_dicts = {}

    def handle(self, *args, **options):
        # sets log level, according to verbosity
        verbosity = options['verbosity']
        if verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        # year
        self.year = options['year']
        if not self.year:
            raise Exception("Missing year parameter")
        self.logger.info("Processing year: {0}".format(self.year))

        # site_url
        site_url = options['site_url']

        # selected indicatori
        indicators_slugs = options['indicators'].split(',')
        indicatori = Indicatore.objects.filter(slug__in=indicators_slugs)

        # selected voices
        voices_slugs = options['voices'].split(',')
        voices = Voce.objects.filter(slug__in=voices_slugs)

        # global variable containing all values
        indicatori_voci_year = {}

        # values for selected indicatori
        self.logger.debug("reading indicatori values")
        for i in indicatori:
            self.logger.debug(
                u" processing indicator: {0}".format(i.denominazione)
            )
            # extracts indicator values for all locations
            iv = ValoreIndicatore.objects.filter(
                indicatore__slug=i.slug, anno=self.year
            ).values(
                'territorio__istat_id', 'territorio__slug', 'valore'
            )
            for v in iv:
                t_id = v['territorio__istat_id']
                t_slug = v['territorio__slug']
                t_url = "{0}/bilanci/{1}?year={2}".format(
                    site_url, t_slug, self.year
                )
                val = v['valore']

                # creates location record if not found
                # with URL and empty values dictionary
                if t_id not in indicatori_voci_year:
                    indicatori_voci_year[t_id] = {'url': t_url, 'values': {}}

                # adds value for indicator
                # indicator ID is prefixed with _i
                # to avoid clashes with voices values
                indicatori_voci_year[t_id]['values']['i_' + str(i.id)] = val

        # values (precapite) from budget voices
        self.logger.debug("adding voci values")
        for vo in voices:
            self.logger.debug(
                u" processing voice: {0}".format(vo.denominazione)
            )
            # extracts voice procapite values for all locations
            vv = ValoreBilancio.objects.filter(
                voce__slug=vo.slug, anno=self.year
            ).values(
                'territorio__istat_id', 'territorio__slug', 'valore_procapite'
            )
            for v in vv:
                t_id = v['territorio__istat_id']
                t_slug = v['territorio__slug']
                t_url = "{0}/bilanci/{1}?year={2}".format(
                    site_url, t_slug, self.year
                )
                val = v['valore_procapite']

                # creates location record if not found
                # with URL and empty values dictionary
                # should not happen, as the're already
                # there, created by the previous loop
                # on indicatori
                if t_id not in indicatori_voci_year:
                    indicatori_voci_year[t_id] = {'url': t_url, 'values': {}}

                # adds value for voice
                # voice ID is prefixed with _v
                # to avoid clashes with indicatori values
                indicatori_voci_year[t_id]['values']['v_' + str(vo.id)] = val

        # csv output
        self.logger.debug(
            " writing output to map_{0}.csv".format(self.year)
        )
        with open("map_{0}.csv".format(self.year), 'wb') as csvfile:
            # define csvkit writer
            writer = csvkit.py2.CSVKitWriter(csvfile, delimiter=";")

            # write header row
            writer.writerow(
                ["istat_id", "url"] +
                [i.denominazione for i in indicatori] +
                [vo.denominazione for vo in voices]
            )

            # write data rows
            for t_id, iv in list(indicatori_voci_year.items()):
                writer.writerow(
                    [t_id, iv['url']] +
                    [
                        "%.2f" % iv['values']['i_' + str(i.id)]
                        if 'i_' + str(i.id) in iv['values']
                        else '0'
                        for i in indicatori
                    ] +
                    [
                        "%.2f" % iv['values']['v_' + str(v.id)]
                        if 'v_' + str(v.id) in iv['values']
                        else '0'
                        for v in voices
                    ]
                )
