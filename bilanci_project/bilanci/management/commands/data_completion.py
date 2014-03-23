# coding=utf-8
from pprint import pprint
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
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
            self.logger.error("Missing function parameter")
            return
        if function not in self.accepted_functions:
            self.logger.error("Function parameter value not accepted")
            return


        ###
        # dry run
        ###

        dryrun = options['dryrun']

        ###
        # cities
        ###

        cities_codes = options['cities']
        self.logger.info("Opening Lista Comuni")
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
                        self.logger.warning("Territorio:{0} doesnt exist, quitting".format(city))
                        continue

                    else:
                        territori.append(territorio)

            else:
                self.logger.error("Missing city parameter")
                return


        if cities_codes.lower() != 'all':
            self.logger.info("Considering cities: {0}".format(cities))

        ###
        # years
        ###
        years = options['years']
        if not years:
            self.logger.error("Missing years parameter")
            return

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year)+1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2013]

        if not years:
            self.logger.error("No suitable year found in {0}".format(years))
            return

        self.logger.info("Considering years: {0}".format(years))
        self.years = years


        if function == 'contesto':
            # set context in postgres db for Comuni

            ###
            # couchdb
            ###

            couchdb_server_alias = options['couchdb_server']
            couchdb_dbname = settings.COUCHDB_NORMALIZED_VOCI_NAME

            if couchdb_server_alias not in settings.COUCHDB_SERVERS:
                self.logger.error("Unknown couchdb server alias.")
                return


            self.logger.info("Connecting to db: {0}".format(couchdb_dbname))
            couchdb = couch.connect(
                couchdb_dbname,
                couchdb_server_settings=settings.COUCHDB_SERVERS[couchdb_server_alias]
            )

            self.set_contesto(couchdb, territori, years, dryrun)

        elif function == 'cluster_mean':
            # computes cluster mean for each value in the simplified tree

            self.set_cluster_mean(years, dryrun)

        elif function == 'per_capita':
            # computes per-capita values
            self.set_per_capita(territori, years, dryrun)

        else:
            self.logger.error("Function not found, quitting")
            return



    def set_per_capita(self, territori, years, dryrun):
        for year in years:
            for territorio in territori:
                self.logger.info("Calculating per-capita value for Comune:{0} yr:{1}".\
                    format(territorio, year)
                )

                # get context data for comune, anno
                try:
                    comune_context = Contesto.objects.get(
                        anno = year,
                        territorio = territorio,
                    )
                except ObjectDoesNotExist:
                    self.logger.error("Context could not be found for Comune:{0} year:{1}".\
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
                    self.logger.warning("Inhabitants is ZERO for Comune:{0} year:{1}, can't calculate per-capita values".\
                        format(territorio, year,)
                        )



        return

    def set_cluster_mean(self, years, dryrun):

        self.logger.info("Cluster mean start")

        for cluster_data in Territorio.CLUSTER:

            self.logger.info("Considering cluster: {0}".format(cluster_data[1]))
            # creates a fake territorio for each cluster if it doens't exist already
            territorio_cluster, is_created = Territorio.objects.\
                get_or_create(
                    denominazione = cluster_data[1],
                    territorio = Territorio.TERRITORIO.L,
                    cluster = cluster_data[0]
                )

            # gets all the territori belonging to the considered cluster
            territori_cluster_set = Territorio.objects.filter(
                territorio = Territorio.TERRITORIO.C,
                cluster = cluster_data[0]
            )

            for voce in Voce.objects.all():
                if voce.is_leaf_node():
                    self.logger.debug("Considering voce: {0}".format(voce))

                    for year in years:
                        self.logger.info("Considering year: {0}".format(year))

                        totale = 0
                        totale_pc = 0
                        n_cities = 0
                        for territorio_in_cluster in territori_cluster_set:

                            try:
                                valore_bilancio =\
                                    ValoreBilancio.objects.get(
                                        territorio = territorio_in_cluster,
                                        anno = year,
                                        voce = voce,
                                    )

                            except ObjectDoesNotExist:
                                self.logger.warning("Voce: {0} doesnt exist for Comune: {1} year:{2} ".format(
                                    voce, territorio_in_cluster, year
                                ))
                            except MultipleObjectsReturned:
                                self.logger.error("Query on Valore bilancio on territorio:{0}, anno:{1}, voce:{2} returned multiple obj".\
                                    format(territorio_in_cluster, year, voce))
                                valore_bilancio_set = ValoreBilancio.objects.filter(
                                        territorio = territorio_in_cluster,
                                        anno = year,
                                        voce = voce,
                                    )

                                pprint(valore_bilancio_set)
                                return

                            else:
                                totale += valore_bilancio.valore
                                totale_pc += valore_bilancio.valore_procapite
                                n_cities += 1

                        if n_cities > 0:
                            media = totale / n_cities
                            valore_media = ValoreBilancio()
                            valore_media.voce = voce
                            valore_media.territorio = territorio_cluster
                            valore_media.anno = year
                            valore_media.valore = media
                            valore_media.save()

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
                            self.logger.warning("Titolo 'quadro-1-dati-generali-al-31-dicembrenotizie-varie' not found for id:{0}, skipping". format(bilancio_id))
                    else:
                        self.logger.warning("Quadro '01' not found for id:{0}, skipping".format(bilancio_id))

                else:
                    self.logger.warning("Bilancio obj not found for id:{0}, skipping". format(bilancio_id))

        if len(missing_territories)>0:
            self.logger.error("Following cities could not be found in Territori DB and could not be processed:")
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



