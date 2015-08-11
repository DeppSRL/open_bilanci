"""
Compute median values for the cluster

Virtual *cluster* locations are created, if non-existing-

Median values are computed either for Voci and Indicatori,
as specified in the --type command-line parameter.
"""
# coding=utf-8

import logging
import math
import numpy
from collections import OrderedDict
from itertools import groupby
from optparse import make_option

from django.db.transaction import set_autocommit, commit, get_autocommit
from django.core.management import BaseCommand
from django.conf import settings

from bilanci.models import Voce, ValoreBilancio, Indicatore, ValoreIndicatore
from territori.models import Territorio, Contesto


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--years',
                    dest='years',
                    default='',
                    help='Years to fetch. From 2003 to 2013. Use one of this formats: 2013 or 2003-2006 or 2003,2004,2006'),
        make_option('--type', '-t',
                    dest='type',
                    default='voci',
                    help='Type of median values to compute. [voci | indicatori]'),
        make_option('--slug', '-s',
                    dest='slug',
                    default=None,
                    help='Indicate the slug of the root node from which to start to calculate median. Includes self.'),
        make_option('--skip-existing',
                    dest='skip_existing',
                    action='store_true',
                    default=False,
                    help='Skip existing cities. Use to speed up long import of many cities, when errors occur'),
        make_option('--autocommit',
                    dest='autocommit',
                    action='store_true',
                    default=False,
                    help='Keeps autocommit enabled: needed for couch2pg mng task calls'),
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

        autocommit = options['autocommit']

        ##
        # starting node slug
        ##

        slug = options['slug']

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
            years = [int(y.strip()) for y in years.split(",") if settings.APP_START_YEAR < int(y.strip()) < settings.APP_END_YEAR]

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


        # gets territori count for that cluster and divides that value by 2:
        # for every value calculated if there are more values than the number stored in cluster_count for that cluster
        # the median value is computed otherwise is skipped

        cluster_count  = dict((k[0], Territorio.objects.filter(territorio="C", cluster=k[0]).count()/2) for k in Territorio.CLUSTER)

        self.logger.info("Cluster median values computation start")
        if autocommit is False:
            set_autocommit(autocommit=False)

        for cluster_data in Territorio.CLUSTER:
            # creates a fake territorio for each cluster if it doens't exist already
            territorio_cluster, is_created = Territorio.objects. \
                get_or_create(
                territorio=Territorio.TERRITORIO.L,
                cluster=cluster_data[0],
            )

            if values_type == 'indicatori':
                for indicatore in Indicatore.objects.all():
                    self.logger.info(u"cluster: {0}, indicatore: {1}".format(territorio_cluster, indicatore.slug))

                    valori_qs = \
                        list(ValoreIndicatore.objects.filter(
                            territorio__territorio='C',
                            territorio__cluster=cluster_data[0],
                            anno__in=years,
                            indicatore=indicatore,
                        ).values('anno', 'valore').order_by('anno'))

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
                        valori = [v for v in valori_dict[year] if v is not None]

                        # the median is saved only if there are enough values for Comuni in the cluster
                        if len(valori) > cluster_count[cluster_data[0]]:
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

                                    if not dryrun:
                                        valore_mediano.save()
                        else:
                            self.logger.debug("No median saved for indicatore:{0}, not enough values for cluster {1}".\
                                format(indicatore.slug, cluster_data[0]))

            if values_type == 'voci':

                voce_set = Voce.objects.all()

                # if slug is specified then considers only descendants of voce with slug=slug including self
                if slug:
                    voce_rootnode = Voce.objects.get(slug = slug)
                    voce_set = voce_rootnode.get_descendants(include_self=True)

                for voce in voce_set:
                    self.logger.info(u"cluster: {0}, voce: {1}".format(territorio_cluster, voce))
                    valori_qs = \
                        ValoreBilancio.objects.filter(
                            territorio__territorio='C',
                            territorio__cluster=cluster_data[0],
                            anno__in=years,
                            voce=voce,
                        ).values('anno', 'valore', 'valore_procapite').order_by('anno')
                    grouped_valori = groupby(valori_qs, key=lambda x: x['anno'])
                    valori_dict = OrderedDict([])
                    valori_procapite_dict = OrderedDict([])
                    for y, v in grouped_valori:
                        valori_dict[y] = []
                        valori_procapite_dict[y] = []
                        for i in list(v):
                            valori_dict[y].append(i['valore'])
                            valori_procapite_dict[y].append(i['valore_procapite'])

                    for year in years:
                        self.logger.debug(u"cluster: {0}, year: {1}, voce: {2}".format(territorio_cluster, year, voce))

                        if year not in valori_dict or valori_dict[year] is None:
                            self.logger.debug(
                                u"No values found for Voce: {0}, year:{1}, cluster:{2}. Median value not computed ".format(
                                    voce, year, cluster_data[0]
                                ))
                            continue

                        # remove null values
                        valori = [v for v in valori_dict[year] if v is not None]
                        valori_procapite = [v for v in valori_procapite_dict[year] if v is not None]

                        # the median is saved only if there are enough values for Comuni in the cluster
                        if len(valori) > cluster_count[cluster_data[0]]:
                            mediana = numpy.median(valori)
                            mediana_procapite = numpy.median(valori_procapite)
                            if not math.isnan(mediana) and not math.isnan(mediana_procapite):
                                valore_mediano, is_created = ValoreBilancio.objects.get_or_create(
                                    voce=voce,
                                    territorio=territorio_cluster,
                                    anno=year,
                                    defaults={
                                        'valore': long(mediana),
                                        'valore_procapite': float(mediana_procapite)
                                    }
                                )

                                # overwrite existing values
                                if not is_created and not skip_existing:
                                    valore_mediano.valore = long(mediana)
                                    valore_mediano.valore_procapite = float(mediana_procapite)

                                    if not dryrun:
                                        valore_mediano.save()

                        else:
                            self.logger.debug(u"No median saved for voce:{0}, not enough values for cluster {1}. {2}<{3}".\
                                format(voce.slug, cluster_data[0], len(valori), cluster_count[cluster_data[0]]))

            if autocommit is False:
                commit()

        if autocommit is False:
            set_autocommit(True)