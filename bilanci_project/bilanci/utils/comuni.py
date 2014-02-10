import re
from django.conf import settings
from bilanci.utils import UnicodeDictReader


class FLMapper(object):
    """
    Has a method to return a list of cities complete (slug--code) finanzalocale identifiers
    from a list of partial elements (slugs or codes).
    """

    def __init__(self, lista_comuni_csv):
        self.lista_comuni_csv = lista_comuni_csv
        self.comuni_dicts = []

    def get_comuni_dicts(self):
        """
        read list of comuni from CSV into a single dictionary
        having the code as key and the slug as value
        """
        try:
            udr = UnicodeDictReader(f=open(self.lista_comuni_csv, mode='r'), dialect="excel_quote_all",)
        except IOError:
            raise Exception("Impossible to open file:%s" % self.lista_comuni_csv)

        comuni_by_codes = {}
        comuni_by_slugs = {}
        for row in udr:
            complete = "{0}--{1}".format(row['NOME_COMUNE'].upper(), row['CODICE_COMUNE'])
            comuni_by_codes[row['CODICE_COMUNE']] = complete
            comuni_by_slugs[row['NOME_COMUNE']] = complete

        return {'codes': comuni_by_codes, 'slugs': comuni_by_slugs}


    _digits = re.compile('\d')
    def contains_digits(self, d):
        return bool(self._digits.search(d))

    def get_cities(self, codes):
        """
        Returns the list of complete names of the cities, used in the html files
        starting from codes or slugs.

        The type of strings passed is automatically guessed.

        Return the complete list, if the All shortcut is used.
        """
        if not self.comuni_dicts:
            self.comuni_dicts = self.get_comuni_dicts()

        if codes.lower() == 'all':
            return self.comuni_dicts['codes'].values()

        codes = [c.strip().upper() for c in codes.split(",")]

        ret = []
        for code in codes:
            try:
                if self.contains_digits(code):
                    # it's a code
                    ret.append(self.comuni_dicts['codes'][code])
                else:
                    # it's a slug
                    ret.append(self.comuni_dicts['slugs'][code])
            except KeyError:
                continue

        return ret


    def get_city(self, code):
        if isinstance(code, list):
            code = code[0]
        return  self.get_cities(code)[0]
