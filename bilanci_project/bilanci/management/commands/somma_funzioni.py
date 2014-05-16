# coding=utf-8

"""
Create a branch of bilancio tree to store the sum of funzioni

 in preventivo create the branch preventivo-spese-spese-somma-funzioni
 in consuntivo create the branch consuntivo-spese--cassa-spese-somma-funzioni
"""
import logging
from optparse import make_option
from django.core.exceptions import ObjectDoesNotExist

from django.core.management import BaseCommand

from bilanci.models import Voce


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (

        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: nothing is written in the db'),
    )

    help = """
        Creates the Somma funzioni branch in the bilancio tree. To be run just once for db instance
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
        # dryrun
        ###
        dryrun = options['dryrun']

        new_branch_denominazione = '_spese_somma_funzioni'
        new_branch_slug_affix = 'spese-somma-funzioni'

        ##
        # insert somma-funzioni in preventivo
        ##
        rootnode_preventivo = Voce.objects.get(slug='preventivo-spese')
        preventivo_funzioni = Voce.objects.get(slug='preventivo-spese-spese-correnti-funzioni')
        
        # create new branch rootnode
        new_preventivo_rootnode = Voce()
        new_preventivo_rootnode.slug=rootnode_preventivo.slug+"-"+new_branch_slug_affix
        new_preventivo_rootnode.denominazione = new_branch_denominazione

        try:
            _= Voce.objects.get(slug=new_preventivo_rootnode.slug)
        except ObjectDoesNotExist:
            pass
        else:
            self.logger.error(u"Voce with slug {0} already exists! Quitting".format(new_preventivo_rootnode.slug))
            return

        self.logger.info(u"Create Voce rootnode {0} {1}".format(new_preventivo_rootnode.denominazione, new_preventivo_rootnode.slug))
        if not dryrun:
            new_preventivo_rootnode.insert_at(rootnode_preventivo, position=u'last-child')
            new_preventivo_rootnode.save()

        # insert leaves for new branch
        
        for f_original in preventivo_funzioni.get_children():
            v_funzione = Voce()
            v_funzione.slug = f_original.slug.replace('spese-correnti-funzioni', 'spese-somma-funzioni')
            v_funzione.denominazione = f_original.denominazione

            self.logger.info(u"Create Voce preventivo {0} {1}".format(v_funzione.denominazione, v_funzione.slug))
            if not dryrun:
                v_funzione.insert_at(new_preventivo_rootnode, position=u'last-child')
                v_funzione.save()


        ##
        # insert somma-funzioni in consuntivo
        ##
        
        rootnode_consuntivo = Voce.objects.get(slug='consuntivo-spese-cassa')
        consuntivo_funzioni = Voce.objects.get(slug='consuntivo-spese-cassa-spese-correnti-funzioni')
        
        # create new branch rootnode
        new_consuntivo_rootnode = Voce()
        new_consuntivo_rootnode.slug=rootnode_consuntivo.slug+"-"+new_branch_slug_affix
        new_consuntivo_rootnode.denominazione = new_branch_denominazione

        try:
            _= Voce.objects.get(slug=new_consuntivo_rootnode.slug)
        except ObjectDoesNotExist:
            pass
        else:
            self.logger.error(u"Voce with slug {0} already exists! Quitting".format(new_preventivo_rootnode.slug))
            return


        self.logger.info(u"Create Voce rootnode {0} {1}".format(new_consuntivo_rootnode.denominazione, new_consuntivo_rootnode.slug))
        if not dryrun:
            new_consuntivo_rootnode.insert_at(rootnode_consuntivo, position=u'last-child')
            new_consuntivo_rootnode.save()
            
        
        # insert leaves for new branch
        
        for first_level_original in consuntivo_funzioni.get_children():
            v_funzione_first = Voce()
            v_funzione_first.slug = first_level_original.slug.replace('spese-correnti-funzioni', 'spese-somma-funzioni')
            v_funzione_first.denominazione = first_level_original.denominazione


            self.logger.info(u"Create Voce consuntivo {0} {1}".format(v_funzione_first.denominazione, v_funzione_first.slug))
            if not dryrun:
                v_funzione_first.insert_at(new_consuntivo_rootnode, position=u'last-child')
                v_funzione_first.save()

            for second_level_original in first_level_original.get_children():
                v_funzione_second = Voce()
                v_funzione_second.slug = second_level_original.slug.replace('spese-correnti-funzioni', 'spese-somma-funzioni')
                v_funzione_second.denominazione = second_level_original.denominazione

                self.logger.info(u"> Create Voce consuntivo {0} {1}".format(v_funzione_second.denominazione, v_funzione_second.slug))
                if not dryrun:
                    v_funzione_second.insert_at(v_funzione_first,position=u'last-child')
                    v_funzione_second.save()
                
        
