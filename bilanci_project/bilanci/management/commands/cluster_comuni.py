# -*- coding: utf-8 -*-
import logging
from optparse import make_option
from pprint import pprint
from django.core.management import BaseCommand
from django.utils.datastructures import SortedDict
from territori.models import Territorio
__author__ = 'stefano'



class Command(BaseCommand):


    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written on db'),

    )

    help = 'Assign to Comuni in Territori a cluster value based on inhabitants'

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

        dryrun = options['dryrun']

        self.logger.info(u"Start cluster values assignment with dryrun: {0}".format(dryrun))

        self.set_cluster_value(dryrun)
        self.logger.info(u"End cluster values script")



    def set_cluster_value(self,dryrun):


        # - fino a 300 abitanti num comuni = 411 cluster = 1 [i più piccoli]
        # - da 301 a 500 abitanti num comuni = 422 cluster = 1 [i più piccoli]
        # - da 501 a 1.000 abitanti num comuni = 1.116 cluster = 2 [molto piccoli]
        # - da 1001 a 3.000 abitanti num comuni = 2.584 cluster = 3 [piccoli 1]
        # - da 3001 a 5.000 abitanti num comuni = 1.152 cluster = 4 [piccoli 2]
        # - da 5001 a 10.000 abitanti num comuni = 1.192 cluster = 5 [medio piccoli]
        # - da 10.001 a 50.000 abitanti num comuni = 1.068 cluster = 6 [medi]
        # - da 50.0001 a 200.000 abitanti num comuni = 134 cluster = 7 [grandi]
        # - da 200.001 a 500.000 abitanti num comuni = 9 cluster = 8 [molto grandi]
        # - oltre i 500.000 abitanti num comuni  =  6 cluster = 9 [i più grandi]


        cluster_map = SortedDict([
            ('1',500),
            ('2',1000),
            ('3',3000),
            ('4',5000),
            ('5',10000),
            ('6',50000),
            ('7',200000),
            ('8',500000),
        ])


        # determina in quale cluster sta il Comune. Se il n.di abitanti e' <= del limite massimo
        # del cluster, allora quello e' il suo cluster di appartenenza
        comuni = Territorio.objects.filter(territorio=Territorio.TERRITORIO.C)

        for comune in comuni:
            cluster_value = None
            for cluster_id,upper_treshold in cluster_map.items():
                if comune.abitanti <= upper_treshold:
                    cluster_value = cluster_id
                    break

            if cluster_value is None:
                cluster_value = '9'

            comune.cluster = cluster_value

            if dryrun is False:
                comune.save()

            self.logger.info(u"Comune: {0}, inhabitants:{1} cluster value:{2} - {3}".\
                format(comune.denominazione,comune.abitanti,comune.cluster,comune.get_cluster_display()))

        return


