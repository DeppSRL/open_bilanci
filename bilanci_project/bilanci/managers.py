from django.core.cache import cache

__author__ = 'guglielmo'
from django.db import models


class ValoriManager(models.Manager):


    def get_classifica_ids(self, item_id, anno):
        """
        Returns the list of Territorio ids ordered by descending valore_procapite or valore
        for the given anno and item (indicatore or voce).
        Read from the cache, if present. Else read from the DB and store it in the cache.

        :param item_id: the ID of the indicatore or voce
        :param anno: integer, contains the anno
        :return: A list of Territorio ids
        """

        # build the key
        key = 'classifiche-{0}-{1}-{2}'.format(
            self.item_type,
            anno,
            item_id
        )

        filters = {
            'anno': anno,
            "{0}__id".format(self.item_type): item_id,
        }
        ids = cache.get(key)
        if ids is None:
            ids = list(
                self.filter(**filters).order_by(self.orderby_label).\
                  values('territorio__id', 'valore')
            )
            cache.set(key, ids)

        return ids


class ValoreBilancioManager(ValoriManager):
    item_type = 'voce'
    orderby_label = '-valore_procapite'

class ValoreIndicatoreManager(ValoriManager):
    item_type = 'indicatore'
    orderby_label = '-valore'
