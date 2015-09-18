"""
nidaba.uzn
~~~~~~~~~~

A simple writer/reader interface for UNLV-style zone files.
"""

from __future__ import unicode_literals, print_function, absolute_import

import csv

from nidaba.nidabaexceptions import NidabaInputException


class UZNReader(object):
    """
    A reader parsing a UNLV zone file from a file object 'f'.
    """

    def __init__(self, f, **kwds):
        self.reader = csv.reader(f, delimiter=' ', skipinitialspace=True, **kwds)

    def next(self):
        row = self.reader.next()
        if len(row) != 5:
            raise NidabaInputException('Incorrect number of columns')
        coords = [int(s) for s in row[:-1]]
        coordinates = [coords[0],
                       coords[1],
                       coords[0] + coords[2],
                       coords[1] + coords[3]]
        return coordinates + [row[-1]]

    def __iter__(self):
        return self


class UZNWriter(object):
    """
    A class writing a UNLV zone file.
    """

    def __init__(self, f, **kwds):
        self.writer = csv.writer(f, delimiter=b' ', **kwds)

    def writerow(self, x0, y0, x1, y1, descriptor='Text'):
        self.writer.writerow([x0, y0, x1 - x0, y1 - y0, descriptor])

    def writerows(self, rows):
        for row in rows:
            self.writerow(*row)
