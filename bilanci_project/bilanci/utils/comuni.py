import csv
import re
from pprint import pprint
from django.conf import settings
import requests
from ..utils import UnicodeDictReader


class CityNameNotUnique(Exception):
    pass


class FLMapper(object):
    """
    Has a method to return a list of cities complete (slug--code) finanzalocale identifiers
    from a list of partial elements (slugs or codes).
    """

    def __init__(self):
        self.lista_comuni_csv = requests.get(settings.S3_LISTA_COMUNI_URL).iter_lines()
        self.comuni_dicts = []

    def get_comuni_dicts(self):
        """
        read list of comuni from CSV (stored in Amazon s3) into a single dictionary
        having the code as key and the slug as value
        """
        try:
            lista_comuni_csv = requests.get(settings.S3_LISTA_COMUNI_URL)
            reader = csv.reader(lista_comuni_csv.iter_lines(), delimiter=',', quotechar='\n')
        except IOError:
            raise Exception("Impossible to open file:%s" % settings.S3_LISTA_COMUNI_URL)

        comuni_by_codes = {}
        comuni_by_slugs = {}

        for row in reader:
            try:
                row_dict = {
                    'NOME_COMUNE': row[0],
                    'SIGLA_PROV': row[1],
                    'CODICE_COMUNE': row[2],
                }
            except IndexError:
                # todo:CSV files has some unexpected empty lines, this is a bug to be fixed
                continue
            complete = "{0}--{1}".format(row_dict['NOME_COMUNE'].upper(), row_dict['CODICE_COMUNE'])

            comuni_by_codes[row_dict['CODICE_COMUNE']] = complete

            # comuni_by_slug is a dictionary containing a dict of elements
            # the key of the inner dict is the provincia_code of the comune
            # es. AGRIGENTO -> key: AG
            # the dict normally has 1 element but if the NOME_COMUNE is not unique then
            # the dict has multiple elements.

            if row_dict['NOME_COMUNE'] not in comuni_by_slugs:
                comuni_by_slugs[row_dict['NOME_COMUNE']] = {}
            comuni_by_slugs[row_dict['NOME_COMUNE']][row_dict["SIGLA_PROV"]] = complete

        return {'codes': comuni_by_codes, 'slugs': comuni_by_slugs, }

    _digits = re.compile('\d')

    def contains_digits(self, d):
        return bool(self._digits.search(d))

    def get_cities(self, codes, logger=None):
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
        code_list = codes.split(",")

        finloc_separator = "--"

        ##
        # Manipulate_codes
        ##
        # strips code string, puts in uppercase
        # if needed
        # transform the complete finloc form COMUNE-NAME--CODFINLOC in CODFINLOC
        def manipulate_codes(code_string):

            code_string = code_string.strip().upper()
            if finloc_separator in code_string:
                code_string = code_string[code_string.index(finloc_separator) + len(finloc_separator):]
            return code_string

        code_list = [manipulate_codes(c) for c in code_list]

        ret = []
        for code in code_list:
            if self.contains_digits(code):
                # it's a code
                try:
                    ret.append(self.comuni_dicts['codes'][code])
                except KeyError:
                    if logger:
                        logger.warning(u"Got key error while processing:{}".format(code))
                    continue
            else:
                # it's a slug

                # if the slug contains a "(" then it's a slug with province code
                if code.find("(") != -1 and code.find(")") != -1:
                    comune_name = code[:code.find("(")]
                    sigla_prov = code[code.find("(") + 1:code.find(")")]
                    try:
                        ret.append(self.comuni_dicts['slugs'][comune_name][sigla_prov])
                    except KeyError:
                        if logger:
                            logger.warning(u"Got key error while processing:{},{}".format(comune_name, sigla_prov))
                        continue
                else:
                    # looks for a comune with a name = code in the dictionary.
                    # if the name is not unique raises an exception

                    # sigla_prov_list is a list of all the provincia code in which Comune with that name
                    # are present
                    # example:
                    # Comune with name "Castro" is present twice in province: "LE" and "BG"
                    # => sigla_prov_list = ["LE","BG"]
                    try:
                        sigla_prov_list = list(self.comuni_dicts['slugs'][code].keys())
                    except KeyError:
                        if logger:
                            logger.warning(u"Got key error while processing:{}".format(code))
                        continue

                    if len(sigla_prov_list) == 1:
                        # se non ha omonimi
                        try:
                            ret.append(self.comuni_dicts['slugs'][code][sigla_prov_list[0]])
                        except KeyError:
                            if logger:
                                logger.warning(u"Got key error while processing:{}".format(code))
                            continue
                    else:
                        # se il comune ha omonimi e la provincia
                        # non e' stata specificata lancia un'eccezione

                        raise CityNameNotUnique(
                            "Comune with name {0} is present in {1} Province:{2}".format(code, len(sigla_prov_list),
                                                                                         sigla_prov_list)
                        )

        return ret

    def get_city(self, code):
        if isinstance(code, list):
            code = code[0]
        return self.get_cities(code)[0]
