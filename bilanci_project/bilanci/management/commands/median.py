"""
Compute median values for the cluster

Virtual *cluster* locations are created, if non-existing-

Median values are computed either for Voci and Indicatori,
as specified in the --type command-line parameter.
"""
# coding=utf-8
from itertools import groupby

import logging
import math
import numpy
from optparse import make_option

from django.core.management import BaseCommand

from bilanci.models import Voce, ValoreBilancio, Indicatore, ValoreIndicatore
from territori.models import Territorio, Contesto


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2002 to 2012. Use one of this formats: 2012 or 2003-2006 or 2002,2004,2006'),
        make_option('--type', '-t',
                    dest='type',
                    default='voci',
                    help='Type of median values to compute. [voci | indicatori]'),
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
        Compute median values for clusters. Can be requested for both voci and indicatori.
        """

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

        ###
        # type
        ###
        values_type = options['type']
        if values_type not in ['voci', 'indicatori']:
            self.logger.error(u"Type parameter not accepted. Choose between 'voci' and 'indicatori'.")
            return

        ###
        # years
        ###
        years = options['years']
        if not years:
            self.logger.error(u"Missing years parameter")
            return

        if "-" in years:
            (start_year, end_year) = years.split("-")
            years = range(int(start_year), int(end_year) + 1)
        else:
            years = [int(y.strip()) for y in years.split(",") if 2001 < int(y.strip()) < 2014]

        if not years:
            self.logger.error(u"No suitable year found in {0}".format(years))
            return

        self.logger.info(u"Considering years: {0}".format(years))
        self.years = years

        ###
        # other options
        ###
        dryrun = options['dryrun']
        skip_existing = options['skip_existing']

        self.logger.info("Cluster median values computation start")
        for cluster_data in Territorio.CLUSTER:
            # creates a fake territorio for each cluster if it doens't exist already
            territorio_cluster, is_created = Territorio.objects. \
                get_or_create(
                denominazione=cluster_data[1],
                territorio=Territorio.TERRITORIO.L,
                cluster=cluster_data[0]
            )

            if values_type == 'indicatori':
                for indicatore in Indicatore.objects.all():
                    self.logger.info(u"cluster: {0}, indicatore: {1}".format(territorio_cluster, indicatore.slug))
                    valori_qs = \
                        ValoreIndicatore.objects.filter(
                            territorio__cluster=cluster_data[0],
                            anno__in=years,
                            indicatore=indicatore,
                        ).values('anno', 'valore').order_by('anno')
                    valori_dict = dict(
                        (k, [i['valore'] for i in list(v)])
                        for k, v in groupby(valori_qs, key=lambda x: x['anno'])
                    )

                    for year in years:
                        self.logger.debug(
                            u"cluster: {0}, year: {1}, indicatore: {2}".format(territorio_cluster, year, indicatore.slug))

                        if year not in valori_dict or valori_dict[year] is None:
                            self.logger.warning(
                                "No values found for Indicatore: {0}, year:{1}. Median value not computed ".format(
                                    indicatore, year
                                ))
                            continue

                        # remove null values
                        valori = [v for v in valori_dict[year] if v]

                        mediana = numpy.median(valori)
                        if not math.isnan(mediana):
                            valore_mediano, is_created = ValoreIndicatore.objects.get_or_create(
                                indicatore=indicatore,
                                territorio=territorio_cluster,
                                anno=year,
                                defaults={
                                    'valore': mediana
                                }
                            )

                            # overwrite existing values
                            if not is_created and not skip_existing:
                                valore_mediano.valore = mediana
                                valore_mediano.save()

            if values_type == 'voci':
                for voce in Voce.objects.all():
                    self.logger.info(u"cluster: {0}, voce: {1}".format(territorio_cluster, voce))
                    valori_qs = \
                        ValoreBilancio.objects.filter(
                            territorio__cluster=cluster_data[0],
                            anno__in=years,
                            voce=voce,
                        ).values('anno', 'valore').order_by('anno')
                    valori_dict = dict(
                        (k, [i['valore'] for i in list(v)])
                        for k, v in groupby(valori_qs, key=lambda x: x['anno'])
                    )

                    for year in years:
                        self.logger.debug(u"cluster: {0}, year: {1}, voce: {2}".format(territorio_cluster, year, voce))


                        if year not in valori_dict or valori_dict[year] is None:
                            self.logger.warning(
                                "No values found for Voce: {0}, year:{1}. Median value not computed ".format(
                                    voce, year
                                ))
                            continue

                        # remove null values
                        valori = [v for v in valori_dict[year] if v]

                        mediana = numpy.median(valori)
                        if not math.isnan(mediana):
                            valore_mediano, is_created = ValoreBilancio.objects.get_or_create(
                                voce=voce,
                                territorio=territorio_cluster,
                                anno=year,
                                defaults={
                                    'valore': long(mediana)
                                }
                            )

                            # overwrite existing values
                            if not is_created and not skip_existing:
                                valore_mediano.valore = long(mediana)
                                valore_mediano.save()
