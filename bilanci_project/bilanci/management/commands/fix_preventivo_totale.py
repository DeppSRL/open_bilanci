"""
Sets values for totale entrate / spese value for Preventivo based on the sum of the 1st level children
"""
# coding=utf-8

import logging
from itertools import groupby
from optparse import make_option

from django.db.transaction import set_autocommit, commit
from django.core.management import BaseCommand
from django.conf import settings

from bilanci.models import Voce, ValoreBilancio
from territori.models import Territorio


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),

    )

    help = """
        Sets values for totale entrate / spese value for Preventivo based on the sum of the 1st level children
        """

    logger = logging.getLogger('management')
    regroup = None
    dryrun = False

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        self.dryrun = options['dryrun']

        if verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        slugset_roots = ['preventivo-entrate', 'preventivo-spese']
        slugset_children = []

        pe_children = Voce.objects.get(slug='preventivo-entrate').get_natural_children().values_list('slug', flat=True)
        ps_children = Voce.objects.get(slug='preventivo-spese').get_natural_children().values_list('slug', flat=True)
        slugset_children.extend(pe_children)
        slugset_children.extend(ps_children)

        data_set = ValoreBilancio.objects.filter(voce__slug__in=slugset_children).\
            select_related().\
            values('anno', 'voce__slug', 'territorio__slug', 'valore','valore_procapite').\
            order_by('anno', 'voce__slug', 'territorio__slug')

        considered_territori = Territorio.objects.filter(territorio="C" ).order_by('-cluster', 'slug')
        considered_years = ValoreBilancio.objects.distinct('anno').order_by('anno').values_list('anno', flat=True)
        keygen = lambda x: (x['anno'], x['voce__slug'], x['territorio__slug'])
        self.regroup = dict((k, list(v)[0]) for k, v in groupby(data_set, key=keygen))

        # delete old values for preventivo-entrate and preventivo-spese
        if self.dryrun is False:
            self.logger.info("Deleting old values for preventivo-entrate,preventivo-spese")
            ValoreBilancio.objects.filter(voce__slug__in=slugset_roots).delete()

        for territorio in considered_territori:
            # in develop: just fix the Territori that have at least 1 valore in db, skip empty ones
            if settings.INSTANCE_TYPE == 'development':
                if ValoreBilancio.objects.filter(territorio=territorio).count() == 0:
                    continue
            self.logger.info("Fixing {}".format(territorio.slug))
            for anno in considered_years:
                self.logger.debug("Fixing anno {}".format(anno))

                self.writes_totale(totale_slug='preventivo-entrate', children_slugs=pe_children, anno=anno, territorio=territorio,)
                self.writes_totale(totale_slug='preventivo-spese', children_slugs=ps_children, anno=anno, territorio=territorio,)

    def writes_totale(self, totale_slug, children_slugs, anno, territorio):

        # writes new totale as sum of 1st level children
        children_valore = 0
        children_valore_procapite = 0

        for child_slug in children_slugs:
            try:
                children_valore += self.regroup[(anno, child_slug, territorio.slug)]['valore']
                children_valore_procapite += self.regroup[(anno, child_slug, territorio.slug)]['valore_procapite']
            except KeyError:
                # self.logger.warning("Territorio:{}, anno:{} Voce:{} has no value, cannot compute:{}".format(territorio.slug, anno, child_slug, totale_slug))
                return

        if self.dryrun is False:
            # writes sum value in the db
            vb = ValoreBilancio()
            vb.territorio = territorio
            vb.anno = anno
            vb.voce = Voce.objects.get(slug=totale_slug)
            vb.valore = children_valore
            vb.valore_procapite = children_valore_procapite

            self.logger.debug("Territorio:{}, anno:{}, voce:{}, valore:{}, vpp:{}".format(territorio.slug, anno, totale_slug, children_valore, children_valore_procapite))

            if self.dryrun is False:
                vb.save()
