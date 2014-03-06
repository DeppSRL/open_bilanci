from _csv import register_dialect, QUOTE_ALL
import csv
import codecs
import cStringIO


class EncodedRecoder:
    """
    Iterator that reads an encoded stream and reencodes the input to the specified encoding
    """
    def __init__(self, f, encoding="utf-8"):
        self.reader = codecs.getreader(encoding)(f)
        self.encoding = encoding

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode(self.encoding)


class UnicodeDictReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = EncodedRecoder(f, encoding)
        self.reader = csv.DictReader(f, dialect=dialect, **kwds)
        self.encoding = encoding

    def next(self):
        row = self.reader.next()
        return dict((k, s.decode(self.encoding)) for k, s in row.iteritems() if s is not None)

    @property
    def columns(self):
        return tuple(self.reader.fieldnames)

    def __iter__(self):
        return self


class UnicodeDictWriter(object):
    def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()
        self.encoding = encoding

    def _unicode_row(self):
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode(self.encoding)
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writeheader(self):
        header = dict(zip(self.writer.fieldnames, self.writer.fieldnames))
        self.writerow(header)

    def writerow(self, D):
        self.writer.writerow(dict([(k, v.encode(self.encoding)) for k, v in D.items()]))
        self._unicode_row()

    def writerow_list(self, L):
        self.writer.writer.writerow([v.encode(self.encoding) for v in L])
        self._unicode_row()

    def writerows(self, rows):
        for D in rows:
            self.writerow(D)


class excel_semicolon(csv.excel):
    """Extends excel Dialect in order to set semicolon as delimiter."""
    delimiter = ';'
    quoting = QUOTE_ALL

register_dialect("excel_semicolon", excel_semicolon)


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()
        self.encoding = encoding

    def writerow(self, row):
        self.writer.writerow([s.encode(self.encoding) for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode(self.encoding)
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
