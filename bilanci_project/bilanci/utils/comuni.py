import re
from django.conf import settings
from ..utils import UnicodeDictReader


class CityNameNotUnique(Exception):
    pass

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

            # comuni_by_slug is a dictionary containing a dict of elements
            # the key of the inner dict is the provincia_code of the comune
            # es. AGRIGENTO -> key: AG
            # the dict normally has 1 element but if the NOME_COMUNE is not unique then
            # the dict has multiple elements.

            if row['NOME_COMUNE'] not in comuni_by_slugs:
                comuni_by_slugs[row['NOME_COMUNE']] = {}
            comuni_by_slugs[row['NOME_COMUNE']][row["SIGLA_PROV"]] = complete


        return {'codes': comuni_by_codes, 'slugs': comuni_by_slugs,}


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
            return sorted(self.comuni_dicts['codes'].values())

        # splits the codes string in cities codes
        # transform the complete finloc form COMUNE-NAME--CODFINLOC in CODFINLOC
        finloc_separator = "--"
        codes = [c.strip().upper() for c in codes.split(",")]
        codes = [c[c.index(finloc_separator)+len(finloc_separator):] if c.index(finloc_separator) != -1 else c for c in codes]


        ret = []
        for code in codes:
            try:
                if self.contains_digits(code):
                    # it's a code
                    ret.append(self.comuni_dicts['codes'][code])
                else:
                    # it's a slug

                    # if the slug contains a "(" then it's a slug with province code
                    if code.find("(") != -1 and code.find(")") != -1:
                        comune_name = code[:code.find("(")]
                        sigla_prov = code[code.find("(")+1:code.find(")")]
                        ret.append(self.comuni_dicts['slugs'][comune_name][sigla_prov])
                    else:
                        # looks for a comune with a name = code in the dictionary.
                        # if the name is not unique raises an exception

                        # sigla_prov_list is a list of all the provincia code in which Comune with that name
                        # are present
                        # example:
                        # Comune with name "Castro" is present twice in province: "LE" and "BG"
                        # => sigla_prov_list = ["LE","BG"]

                        sigla_prov_list = list(self.comuni_dicts['slugs'][code].keys())
                        if len(sigla_prov_list) == 1:
                            # se non ha omonimi
                            ret.append(self.comuni_dicts['slugs'][code][sigla_prov_list[0]])
                        else:
                            # se il comune ha omonimi e la provincia
                            # non e' stata specificata lancia un'eccezione

                            raise CityNameNotUnique("Comune with name {0} is present in {1} Province:{2}".\
                                format(code, len(sigla_prov_list), sigla_prov_list ))

            except KeyError:
                continue

        return ret


    def get_city(self, code):
        if isinstance(code, list):
            code = code[0]
        return  self.get_cities(code)[0]
