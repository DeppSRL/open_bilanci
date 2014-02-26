# -*- coding: utf-8 -*-
import logging
from optparse import make_option
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.text import slugify
import requests
from bilanci.utils.comuni import FLMapper
from territori.models import Territorio
__author__ = 'stefano'



class Command(BaseCommand):


    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written on db'),
        make_option('--api-domain',
                    dest='apidomain',
                    default='api3.staging.deppsviluppo.org',
                    help='The domain of the API. Defaults to api3.staging.deppsviluppo.org'),
        make_option('--auth',
                    dest='auth',
                    default='',
                    help='Auth, as user,pass. Separated by a comma, no space.'),
        make_option('--limit',
                    dest='limit',
                    default=0,
                    help='Limit of records to import'),
        make_option('--offset',
                    dest='offset',
                    default=0,
                    help='Offset of records to start from'),

    )

    help = 'Assign finanza locale codes to each municipality'

    logger = logging.getLogger('management')
    baseurl = None
    dryrun = None
    apidomain = None



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

        offset = int(options['offset'])
        limit = int(options['limit'])

        self.dryrun = options['dryrun']
        self.apidomain = options['apidomain']
        if options['auth']:
            (user, pwd) = options['auth'].split(",")
            self.baseurl = "http://{0}:{1}@{2}".format(user, pwd, self.apidomain)
        else:
            self.baseurl = "http://{0}".format(self.apidomain)

        self.logger.info(u"=== Starting ===")

        # all cities in the DB
        comuni = Territorio.objects.filter(territorio=Territorio.TERRITORIO.C)

        mapper = FLMapper(settings.LISTA_COMUNI_PATH)

        c = 0
        for comune in comuni:
            c += 1
            if c < offset:
                continue
            if limit and c >= limit + offset:
                break
            city_url = "{0}/maps/places/{1}".format(self.baseurl, comune.slug)
            self.logger.debug("CITY_URL: {0}".format(city_url))
            place = requests.get(city_url).json()

            # get identifiers needed and build the finloc code
            identifiers = place['placeidentifiers']
            macroregion_id = None
            region_id = None
            province_id = None
            city_id = None
            for i in identifiers:
                identifier = i['identifier']
                value = i['value']
                if 'istat-macroregion-id' in identifier:
                    macroregion_id = int(value)
                if 'minint-region-id' in identifier:
                    region_id = int(value)
                if 'minint-province-id' in identifier:
                    province_id = int(value)
                if 'minint-city-id' in identifier:
                    city_id = int(value)


            # build numeric code for finanzalocale
            num_cod_finloc = "{0:d}{1:02d}{2:03d}{3:04d}".format(
                macroregion_id, region_id, province_id, city_id
            )

            # store complete finloc code inside the database
            try:
                comune.cod_finloc = mapper.get_city(num_cod_finloc)
            except IndexError:
                name = "-".join(comune.slug.split('-')[:-2])
                try:
                    comune.cod_finloc = mapper.get_city(name)
                except IndexError:
                    try:
                        denominazione = comune.denominazione.replace("'", " ")
                        name = slugify(denominazione)
                        comune.cod_finloc = mapper.get_city(name)
                    except IndexError:
                        self.logger.warning("Could not find city: {0}".format(comune.slug))
                        continue

            self.logger.info(u"{0}, slug: {1.slug}, cod_finloc: {1.cod_finloc}".format(
                c, comune
            ))


            if not self.dryrun:
                comune.save()




        self.logger.info(u" === End ===")




