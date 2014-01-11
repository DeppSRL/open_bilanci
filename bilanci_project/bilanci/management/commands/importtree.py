# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from optparse import make_option
import logging
import yaml
from bilanci.models import Voce

__author__ = 'guglielmo'



class Command(BaseCommand):
    """
    Import data from yaml file into a tree
    """
    help = "Import data from a yaml file into a given MPTT tree, under a specified node (or root)"

    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: no actual import is made'),
        make_option('--yaml-file',
                    dest='yamlfile',
                    default='./tree.yml',
                    help='Select yaml file'),
        make_option('--node-key',
                    dest='nodekey',
                    default='',
                    help='Key of the node to add the tree to. Leabve blank to add to root level.'),

    )

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

        f_yaml = open(options['yamlfile'], 'r')
        tree = yaml.load(f_yaml.read())
        nodekey = options['nodekey']
        node = None
        if nodekey:
            node = Voce.objects.get(denominazione=options['nodekey'])
        self.add_tree(tree, node)
        f_yaml.close()

    ##
    # generic recursive method to add elements to tree
    ##
    def add_tree(self, tree, parent_node):
        for element in tree:
            if isinstance(element, dict):
                for key, label in element.iteritems():
                    self.logger.info(u"{0}:{1}".format(parent_node,key))
                    node = self.add_node_to_mptt(key, parent_node)
                    self.add_tree(label, node)
            else:
                self.logger.info(u"{0}:{1}".format(parent_node, element))
                self.add_node_to_mptt(element, parent_node)

    ##
    # methods binding to the real MPTT tree instance (Voce)
    ##
    def add_node_to_mptt(self, label, parent_node=None):
        """
        Add an mptt tree element to a given node
        """
        v = Voce(denominazione=label)
        Voce.objects.insert_node(v, parent_node)
        v.save()
        return v
