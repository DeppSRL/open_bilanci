# -*- coding: utf-8 -*-
import json
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from optparse import make_option
import logging
import requests
from territori.models import Territorio

__author__ = 'guglielmo'



class Command(BaseCommand):
    """
    Import territori from OP API
    """
    help = "Import territori data from openpolis API"

    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: no actual import is made'),
        make_option('--api-domain',
                    dest='apidomain',
                    default='api3.staging.deppsviluppo.org',
                    help='The domain of the API. Defaults to api3.staging.deppsviluppo.org'),
        make_option('--auth',
                    dest='auth',
                    default='',
                    help='Auth, as user,pass. Separated by a comma, no space.'),
        make_option('--classification',
                    dest='classification',
                    default='istat-reg',
                    help='The classification slug. Defaults to istat-reg.'),
    )

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
        if options['auth']:
            (user, pwd) = options['auth'].split(",")
            self.baseurl = "http://{0}:{1}@{2}".format(user, pwd, self.apidomain)
        else:
            self.baseurl = "http://{0}".format(self.apidomain)

        classification = options['classification']

        cl = requests.get("{0}/maps/classifications/{1}".format(self.baseurl, classification)).json()
        eu = requests.get(cl['root_node']).json()
        it = requests.get(eu['children'][0]).json()

        it_place = requests.get(it['place']['_self']).json()
        self.add_place(it_place)

        regions_urls = it['children']
        for region_url in regions_urls:
            region = requests.get(region_url).json()
            region_place = requests.get(region['place']['_self']).json()
            self.add_place(region_place)

            provinces_urls = region['children']
            for prov_url in provinces_urls:
                prov = requests.get(prov_url).json()
                prov_place = requests.get(prov['place']['_self']).json()
                self.add_place(prov_place)

                cities_urls = prov['children']
                for city_url in cities_urls:
                    city = requests.get(city_url).json()
                    city_place = requests.get(city['place']['_self']).json()
                    self.add_place(city_place, parent_url=city['parent'])


    def add_place(self, place, parent_url=None):
        slug = place['slug']

        if self.dryrun:
            self.logger.info(
                u": {0} - dryrun".format(slug)
            )
            return

        denominazione = place['name']
        abitanti = place['inhabitants']
        tipo_territorio = self.get_tipo_territorio(place['place_type'])
        defaults = {
            'territorio': tipo_territorio,
            'denominazione': denominazione,
            'abitanti': abitanti,
        }

        # identifiers
        identifiers = place['placeidentifiers']
        for i in identifiers:
            if i == "http://{0}/maps/identifiers/istat-region-id".format(self.apidomain):
                defaults['cod_reg'] = i.value
            if i == "http://{0}/maps/identifiers/istat-province-id".format(self.apidomain):
                defaults['cod_prov'] = i.value
            if i == "http://{0}/maps/identifiers/istat-city-id".format(self.apidomain):
                defaults['cod_com'] = i.value

        # geometry features
        geom = place['geoinfo']['geom']
        if geom is not None:
            defaults['geom'] = GEOSGeometry(json.dumps(geom))

        # acronym for cities
        if tipo_territorio == 'C':
            prov = requests.get(parent_url).json()
            prov_place = requests.get(prov['place']['_self']).json()
            defaults['prov'] = prov_place['acronym']

        t, created = Territorio.objects.get_or_create(
            slug=slug,
            defaults=defaults
        )
        if created:
            self.logger.info(
                u"New place added: {0}".format(slug)
            )
        else:
            t.denominazione = denominazione
            t.territorio = tipo_territorio
            t.abitanti = abitanti
            if 'cod_reg' in defaults:
                t.cod_reg = defaults['cod_reg']
            if 'cod_prov' in defaults:
                t.cod_prov = defaults['cod_prov']
            if 'cod_com' in defaults:
                t.cod_com = defaults['cod_com']
            if 'geom' in defaults:
                t.geom = defaults['geom']
            if 'prov' in defaults:
                t.prov = defaults['prov']
            t.save()
            self.logger.info(
                u"Place overwritten: {0}".format(slug)
            )



    def get_tipo_territorio(self, place_type_url):
        t = requests.get(place_type_url).json()
        return t['name'][0]