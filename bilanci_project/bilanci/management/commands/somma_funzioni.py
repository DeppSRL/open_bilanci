# coding=utf-8

"""
Create a branch of bilancio tree to store the sum of funzioni

 in preventivo create the branch preventivo-spese-spese-somma-funzioni
 in consuntivo create the branch consuntivo-spese-cassa-spese-somma-funzioni
 in consuntivo create the branch consuntivo-spese-impegni-spese-somma-funzioni
"""
import logging
from django.core.exceptions import ObjectDoesNotExist
from bilanci.models import Voce


class SommaFunzioniMixin(object):

    """
        Creates the Somma funzioni branch in the bilancio tree. To be run just once for db instance
    """

    logger = logging.getLogger('management')
    new_branch_denominazione = '_spese_somma_funzioni'
    new_branch_slug_affix = 'spese-somma-funzioni'


    def create_branch_consuntivo(self, rootnode_slug):

        rootnode_consuntivo = Voce.objects.get(slug=rootnode_slug)
        consuntivo_funzioni = Voce.objects.get(slug=rootnode_slug+'-spese-correnti-funzioni')

        # create new branch rootnode
        new_consuntivo_rootnode = Voce()
        new_consuntivo_rootnode.slug=rootnode_consuntivo.slug+"-"+self.new_branch_slug_affix
        new_consuntivo_rootnode.denominazione = self.new_branch_denominazione

        try:
            _= Voce.objects.get(slug=new_consuntivo_rootnode.slug)
        except ObjectDoesNotExist:
            pass
        else:
            self.logger.error(u"Voce with slug {0} already exists! Quitting".format(new_consuntivo_rootnode.slug))
            return


        self.logger.info(u"Create Voce rootnode {0} {1}".format(new_consuntivo_rootnode.denominazione, new_consuntivo_rootnode.slug))
        new_consuntivo_rootnode.insert_at(rootnode_consuntivo, position=u'last-child')
        new_consuntivo_rootnode.save()


        # insert leaves for new branch

        for first_level_original in consuntivo_funzioni.get_children():
            v_funzione_first = Voce()
            v_funzione_first.slug = first_level_original.slug.replace('spese-correnti-funzioni', 'spese-somma-funzioni')
            v_funzione_first.denominazione = first_level_original.denominazione


            self.logger.info(u"Create Voce consuntivo {0} {1}".format(v_funzione_first.denominazione, v_funzione_first.slug))
            v_funzione_first.insert_at(new_consuntivo_rootnode, position=u'last-child')
            v_funzione_first.save()

            for second_level_original in first_level_original.get_children():
                v_funzione_second = Voce()
                v_funzione_second.slug = second_level_original.slug.replace('spese-correnti-funzioni', 'spese-somma-funzioni')
                v_funzione_second.denominazione = second_level_original.denominazione

                self.logger.info(u"> Create Voce consuntivo {0} {1}".format(v_funzione_second.denominazione, v_funzione_second.slug))
                v_funzione_second.insert_at(v_funzione_first,position=u'last-child')
                v_funzione_second.save()


    def create_branch_preventivo(self):
        ##
        # insert somma-funzioni in preventivo
        ##
        rootnode_preventivo = Voce.objects.get(slug='preventivo-spese')
        preventivo_funzioni = Voce.objects.get(slug='preventivo-spese-spese-correnti-funzioni')

        # create new branch rootnode
        new_preventivo_rootnode = Voce()
        new_preventivo_rootnode.slug=rootnode_preventivo.slug+"-"+self.new_branch_slug_affix
        new_preventivo_rootnode.denominazione = self.new_branch_denominazione

        try:
            _= Voce.objects.get(slug=new_preventivo_rootnode.slug)
        except ObjectDoesNotExist:
            pass
        else:
            self.logger.error(u"Voce with slug {0} already exists! Quitting".format(new_preventivo_rootnode.slug))
            return

        self.logger.info(u"Create Voce rootnode {0} {1}".format(new_preventivo_rootnode.denominazione, new_preventivo_rootnode.slug))
        new_preventivo_rootnode.insert_at(rootnode_preventivo, position=u'last-child')
        new_preventivo_rootnode.save()

        # insert leaves for new branch
        for f_original in preventivo_funzioni.get_children():
            v_funzione = Voce()
            v_funzione.slug = f_original.slug.replace('spese-correnti-funzioni', 'spese-somma-funzioni')
            v_funzione.denominazione = f_original.denominazione

            self.logger.info(u"Create Voce preventivo {0} {1}".format(v_funzione.denominazione, v_funzione.slug))
            v_funzione.insert_at(new_preventivo_rootnode, position=u'last-child')
            v_funzione.save()

    def create_somma_funzioni(self):

        # insert somma-funzioni in preventivo
        self.create_branch_preventivo()

        # insert somma-funzioni in consuntivo cassa / impegni
        self.create_branch_consuntivo('consuntivo-spese-cassa')
        self.create_branch_consuntivo('consuntivo-spese-impegni')
        return