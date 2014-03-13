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

    help = 'Assign openpolis codes to each municipality'

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

        self.dryrun = options['dryrun']
        self.apidomain = options['apidomain']

        offset = int(options['offset'])
        limit = int(options['limit'])

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
            self.logger.info("{} - Setting op_id for {}".format(c, comune))

            # prende lo slug del comune
            # fa una richiesta alle api di openpolis
            city_url = "{0}/maps/places/{1}".format(self.baseurl, comune.slug)
            api_request = requests.get(city_url)
            json_data = api_request.json()
            op_id = json_data['placeidentifiers'][0]['value']
            # salva openpolis_id nel db
            comune.op_id = op_id
            if not self.dryrun:
                comune.save()




        self.logger.info(u" === End ===")




