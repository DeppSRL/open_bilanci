# coding=utf-8
from pprint import pprint
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import Avg
from bilanci.models import Voce, ValoreBilancio
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio, Contesto
from bilanci.utils import couch


class Command(BaseCommand):

    accepted_functions = ['contesto','cluster_mean','per_capita']

    option_list = BaseCommand.option_list + (
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--cities',
                    dest='cities',
                    default='',
                    help="""
                        Cities codes or slugs. Use comma to separate values: Roma,Napoli,Torino or  "All".
                        NOTE: Cities are considered only for set_contesto function
                        """),
        make_option('--function','-f',
                    dest='function',
                    action='store',
                    default='',
                    help='Function to run: '+  ' | '.join(accepted_functions)),

        make_option('--couchdb-server',
                    dest='couchdb_server',
                    default=settings.COUCHDB_DEFAULT_SERVER,
                    help='CouchDB server to connect to (defaults to staging).'),

        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing cities. Use to speed up long import of many cities, when errors occur'),

        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),

    )

    help = """
        Compute additional necessary data for the Bilanci db: set Comuni context, mean value for Comuni clusters,
        per-capita Bilanci values and Political administration values
        """

    logger = logging.getLogger('management')
    comuni_dicts = {}


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

        ###
        # function
        ###
        function = options['function']
        if not function:
            self.logger.error(u"Missing function parameter")
            return
        if function not in self.accepted_functions:
            self.logger.error(u"Function parameter value not accepted")
            return


        ###
        # dry run
        ###

        dryrun = options['dryrun']
        skip_existing = options['skip_existing']


        ###
        # cities
        ###

        cities_codes = options['cities']
        self.logger.info(u"Opening Lista Comuni")
        mapper = FLMapper(settings.LISTA_COMUNI_PATH)

        # function cluster_mean doesn't need territori param
        cities = None
        if function != 'cluster_mean':
            if cities_codes:
                cities = mapper.get_cities(cities_codes)

                # transforms the list of codfinloc in territori list
                territori = []
                for city in cities:
                    try:
                        territorio = Territorio.objects.get(
                            territorio = 'C',
                            cod_finloc = city,
                        )
                    except ObjectDoesNotExist:
                        self.logger.warning(u"Territorio:{0} doesnt exist, quitting".format(city))
                        continue

                    else:
                        territori.append(territorio)

            else:
                self.logger.error(u"Missing city parameter")
                return


        if cities_codes.lower() != 'all':
            self.logger.info(u"Considering cities: {0}".format(cities))

        ###
        # years
        ###
        years = options['years']
        if not years:
            self.logger.error(u"Missing years parameter")
            return

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year)+1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            self.logger.error(u"No suitable year found in {0}".format(years))
            return

        self.logger.info(u"Considering years: {0}".format(years))
        self.years = years


        if function == 'contesto':
            # set context in postgres db for Comuni

            ###
            # couchdb
            ###

            couchdb_server_alias = options['couchdb_server']
            couchdb_dbname = settings.COUCHDB_NORMALIZED_VOCI_NAME

            if couchdb_server_alias not in settings.COUCHDB_SERVERS:
                self.logger.error(u"Unknown couchdb server alias.")
                return


            self.logger.info(u"Connecting to db: {0}".format(couchdb_dbname))
            couchdb = couch.connect(
                couchdb_dbname,
                couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
            )

            self.set_contesto(couchdb, territori, years, dryrun)

        elif function == 'cluster_mean':
            # computes cluster mean for each value in the simplified tree

            self.set_cluster_mean(years, dryrun, skip_existing=skip_existing)

        elif function == 'per_capita':
            # computes per-capita values
            self.set_per_capita(territori, years, dryrun)

        else:
            self.logger.error(u"Function not found, quitting")
            return



    def set_per_capita(self, territori, years, dryrun):
        for year in years:
            for territorio in territori:
                self.logger.info(u"Calculating per-capita value for Comune:{0} yr:{1}".\
                    format(territorio, year)
                )

                # get context data for comune, anno
                try:
                    comune_context = Contesto.objects.get(
                        anno = year,
                        territorio = territorio,
                    )
                except ObjectDoesNotExist:
                    self.logger.error(u"Context could not be found for Comune:{0} year:{1}".\
                        format(territorio, year,)
                    )
                    continue

                n_abitanti = comune_context.bil_popolazione_residente

                if n_abitanti > 0:
                    voci = ValoreBilancio.objects.filter(
                        anno = year,
                        territorio = territorio,
                    )
                    # for all the Voce in bilancio
                    # calculates the per_capita value

                    for voce in voci:
                        voce.valore_procapite = voce.valore / float(n_abitanti)

                        # writes on db
                        if dryrun is False:
                            voce.save()

                else:
                    self.logger.warning(u"Inhabitants is ZERO for Comune:{0} year:{1}, can't calculate per-capita values".\
                        format(territorio, year,)
                        )



        return

    def set_cluster_mean(self, years, dryrun, skip_existing=False):
        """
        Compute average values.

        Virtual locations are created, holding average values for every Voce and Year.

        """

        self.logger.info("Cluster mean start")

        for cluster_data in Territorio.CLUSTER:

            self.logger.info(u"Considering cluster: {0}".format(cluster_data[1]))
            # creates a fake territorio for each cluster if it doens't exist already
            territorio_cluster, is_created = Territorio.objects.\
                get_or_create(
                    denominazione = cluster_data[1],
                    territorio = Territorio.TERRITORIO.L,
                    cluster = cluster_data[0]
                )

            for voce in Voce.objects.all():
                if voce.is_leaf_node():
                    self.logger.debug(u"Considering voce: {0}".format(voce))

                    for year in years:
                        self.logger.info(u"Considering year: {0}".format(year))

                        media_valore =\
                            ValoreBilancio.objects.filter(
                                territorio__cluster = cluster_data[0],
                                anno = year,
                                voce = voce,
                            ).aggregate(avg = Avg('valore'))['avg']

                        if media_valore is None:
                            self.logger.warning("No values found for Voce: {0}, year:{1}. Average not computed ".format(
                                voce, year
                            ))

                        valore_medio, is_created = ValoreBilancio.objects.get_or_create(
                            voce=voce,
                            territorio=territorio_cluster,
                            anno=year,
                            defaults={
                                'valore': media_valore
                            }
                        )

                        # overwrite existing values
                        if not is_created and not skip_existing:
                            valore_medio.valore = media_valore
                            valore_medio.save()

        return

    def set_contesto(self, couchdb, territori, years, dryrun):
        missing_territories = []

        for territorio in territori:
            for year in years:
                self.logger.info(u"Setting Comune: {0}, year:{1}".format(territorio,year))

                bilancio_id = "{0}_{1}".format(year, territorio.cod_finloc)
                # read data from couch
                if bilancio_id in couchdb:
                    bilancio_data = couchdb[bilancio_id]
                    if "01" in bilancio_data['consuntivo']:
                        if "quadro-1-dati-generali-al-31-dicembrenotizie-varie" in bilancio_data["consuntivo"]["01"]:
                            contesto_couch = bilancio_data["consuntivo"]["01"]\
                                ["quadro-1-dati-generali-al-31-dicembrenotizie-varie"]["data"]

                            # if the contesto data is not present, inserts the data in the db
                            # otherwise skips
                            contesto_pg = None
                            try:
                                contesto_pg = Contesto.objects.get(
                                    anno = year,
                                    territorio = territorio,
                                )
                            except ObjectDoesNotExist:
                                contesto_pg = Contesto()
                                pass

                            # write data on postgres
                            if dryrun is False:


                                # contesto_keys maps the key in the couch doc and the name of
                                # the field in the model

                                contesto_keys = {
                                    "popolazione residente (ab.)":"bil_popolazione_residente",
                                    "nuclei familiari (n)":"bil_nuclei_familiari",
                                    "superficie urbana (ha)":"bil_superficie_urbana",
                                    "superficie totale del comune (ha)":"bil_superficie_totale",
                                    "lunghezza delle strade esterne (km)":"bil_strade_esterne",
                                    "lunghezza delle strade interne centro abitato (km)":"bil_strade_interne",
                                    "di cui: in territorio montano (km)":"bil_strade_montane",
                                    }

                                for contesto_key, contesto_value in contesto_keys.iteritems():
                                    if contesto_key in contesto_couch:
                                        setattr(contesto_pg, contesto_value, clean_data(contesto_couch[contesto_key]))

                                contesto_pg.territorio = territorio
                                contesto_pg.anno = year

                                contesto_pg.save()



                        else:
                            self.logger.warning(u"Titolo 'quadro-1-dati-generali-al-31-dicembrenotizie-varie' not found for id:{0}, skipping". format(bilancio_id))
                    else:
                        self.logger.warning(u"Quadro '01' not found for id:{0}, skipping".format(bilancio_id))

                else:
                    self.logger.warning(u"Bilancio obj not found for id:{0}, skipping". format(bilancio_id))

        if len(missing_territories)>0:
            self.logger.error(u"Following cities could not be found in Territori DB and could not be processed:")
            for missing_city in missing_territories:
                self.logger.error("{0}".format(missing_city))


def clean_data(data):
    c_data = data[0]
    if c_data:
        if c_data == "N.C.":
            return None
        else:
            # if the number contains a comma, it strips the decimal values
            if c_data.find(",") != -1:
                c_data = c_data[:c_data.find(",")]

            # removes the thousand-delimiter point and converts to int
            ret =  int(c_data.replace(".",""))

            if ret > 10 * 1000 * 1000:
                return None
            else:
                return ret



