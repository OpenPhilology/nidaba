# -*- coding: utf-8 -*-
import os
import re
import numpy
import codecs
import operator
import time
from kitchen.text.converters import to_unicode, to_bytes
from lxml import etree


# ----------------------------------------------------------------------
# Exceptions -----------------------------------------------------------
# ----------------------------------------------------------------------

class UnibarrierException(Exception):
    """
    An exception for the unibarrier decorator function.
    """
    def __init__(self, message=None):
        Exception.__init__(self, message)

class AlgorithmException(Exception):
    """
    A simple exception for algorithm specific errors.
    """
    def __init__(self, message=None):
        Exception.__init__(self, message)

# ----------------------------------------------------------------------
# String and alignment algorithms --------------------------------------
# ----------------------------------------------------------------------

def initmatrix(rows, columns, defaultval=0):
    """Initializes a 2d list to the desired dimensions."""
    return [[defaultval for j in xrange(columns)] for i in xrange(rows)]

def mr(matrix):
    """Returns a string rep of a 2d list as a matrix. Useful for 
    debugging."""
    if matrix == []: return '[]'
    string = '['
    count = 0
    for row in matrix:
        if count >= 1: string += ' '
        string += str(row) + '\n'
        count += 1
    string = string[:-1]
    string += ']'
    return string

def native_backtrace(matrix, start=None):
    """Trace edit steps backward to find an edit sequence for an
    alignment. Starts at the provided 'start' index, or in the i,j'th
    index if none is provided. The backtrace always ends
    at the index 0,0."""
    i,j = start if start is not None else (len(matrix)-1, len(matrix[0])-1)
    key = {'i':(0,-1), 'd':(-1,0), 'm':(-1,-1), 's':(-1, -1)}
    path = []

    while matrix[i][j] != '':
        path.insert(0, matrix[i][j])
        i,j = tuple(map(operator.add, (i,j), key[matrix[i][j]]))

    return path

def native_align(str1, str2, substitutionscore=1, insertscore=1, deletescore=1,
                 charmatrix={}):
    """Calculate the edit distance of two strings, then backtrace to
    find a valid edit sequence."""
    matrix, steps = native_full_edit_distance(str1, str2,
                                              substitutionscore=substitutionscore,
                                              insertscore=insertscore,
                                              deletescore=deletescore,
                                              charmatrix=charmatrix)
    return native_backtrace(steps)

def native_semi_global_align(shortseq, longseq, substitutionscore=1,
                             insertscore=1, deletescore=1, charmatrix={}):
    if len(shortseq) > len(longseq):
        raise AlgorithmException('shortseq must be <= longseq in length!')

    matrix, steps = native_full_edit_distance(shortseq, longseq,
                                              substitutionscore=substitutionscore,
                                              insertscore=insertscore,
                                              deletescore=deletescore,
                                              charmatrix=charmatrix,
                                              alignment_type='semi-global')
    return native_backtrace(steps, start=(len(matrix)-1, matrix[-1].index(min(matrix[-1]))))



def native_global_matrix(str1, str2, substitutionscore, insertscore,
                         deletescore, charmatrix):
    """An initial matrix for a global sequence alignment."""
    matrix = initmatrix(len(str1)+1, len(str2)+1)
    for i in xrange(1, len(matrix)):
        matrix[i][0] = i*charmatrix.get(('', str1[i-1]), deletescore)
    for j in xrange(1, len(matrix[0])):
        matrix[0][j] = j*charmatrix.get((str2[j-1], ''), insertscore)
    return matrix

def native_semi_global_matrix(str1, str2, substitutionscore, insertscore,
                              deletescore, charmatrix):
    matrix = initmatrix(len(str1)+1, len(str2)+1)
    for i in xrange(1, len(matrix)):
        matrix[i][0] = i*charmatrix.get(('', str1[i-1]), deletescore)
    return matrix


def native_full_edit_distance(str1, str2, substitutionscore=1, insertscore=1,
                              deletescore=1, charmatrix={},
                              alignment_type='global'):
    """A modified implenmentation of the Wagner-Fischer algorithm using
    numpy. This should be used when an alignment is desired,
    not only the edit distance."""

    types = {'global': native_global_matrix,
             'semi-global':native_semi_global_matrix}
    matrix = types[alignment_type](str1, str2, substitutionscore, insertscore,
                                   deletescore, charmatrix)

    steps = initmatrix(len(str1)+1, len(str2)+1, defaultval='')
    steps[0][1:] = list('i'*(len(str2)))
    for idx in xrange(1, len(matrix)): steps[idx][0] = 'd'
    for i in xrange(1, len(matrix)):
        for j in xrange(1, len(matrix[0])):
            c1 = str1[i-1]
            c2 = str2[j-1]

            scores = (('s', matrix[i-1][j-1] + charmatrix.get((c1, c2), substitutionscore)),
                      ('i', matrix[i][j-1] + charmatrix.get((c1, c2), insertscore)), 
                      ('d', matrix[i-1][j] + charmatrix.get((c1, c2), deletescore)))
            if str1[i-1] == str2[j-1]:
                matrix[i][j] = matrix[i-1][j-1]
                steps[i][j] = 'm'
            else:
                bestoption = min(scores, key=lambda x: x[1])
                matrix[i][j] = bestoption[1]
                steps[i][j] = bestoption[0]

    return matrix, steps

def edit_distance(str1, str2, substitutionscore=1, insertscore=1,
                         deletescore=1, charmatrix={},
                         alignment_type='global'):
    m = native_full_edit_distance(str1, str2,
                                  substitutionscore=substitutionscore,
                                  insertscore=insertscore,
                                  deletescore=deletescore,
                                  charmatrix=charmatrix,
                                  alignment_type=alignment_type)[0]
    return m[-1][ -1]

# ----------------------------------------------------------------------
# String and alignment algorithms (numpy versions) ---------------------
# ----------------------------------------------------------------------

def np_backtrace(matrix, start=None):
    """Trace edit steps backward to find an edit sequence for an
    alignment. Starts at the provided 'start' index, or in the i,j'th
    index if none is provided. The backtrace always ends
    at the index 0,0."""

    i,j = start if start is not None else (matrix.shape[0]-1, matrix.shape[1]-1)
    key = {'i':(0,-1), 'd':(-1,0), 'm':(-1,-1), 's':(-1, -1)}
    path = []

    while matrix[i,j] != '':
        path.insert(0, matrix[i,j])
        i,j = tuple(map(operator.add, (i,j), key[matrix[i,j]]))

    return path

def np_align(str1, str2, substitutionscore=1, insertscore=1, deletescore=1, 
          charmatrix={}):
    """Calculate the edit distance of two strings, then backtrace to
    find a valid edit sequence."""
    matrix, steps = np_full_edit_distance(str1, str2,
                                       substitutionscore=substitutionscore,
                                       insertscore=insertscore,
                                       deletescore=deletescore,
                                       charmatrix=charmatrix)
    return np_backtrace(steps)

def np_semi_global_align(shortseq, longseq, substitutionscore=1, insertscore=1,
                      deletescore=1, charmatrix={}):
    """Find a semi-global alignment between two strings."""
    if len(shortseq) > len(longseq):
        raise AlgorithmException('shortseq must be <= longseq in length!')

    matrix, steps = np_full_edit_distance(shortseq, longseq,
                                       substitutionscore=substitutionscore,
                                       insertscore=insertscore,
                                       deletescore=deletescore,
                                       charmatrix=charmatrix,
                                       alignment_type='semi-global')
    back = np_backtrace(steps, start=(matrix.shape[0]-1,
                                   numpy.argmin(matrix[-1:])))
    return back

def np_global_matrix(str1, str2, substitutionscore, insertscore, deletescore,
                  charmatrix):
    """An initial matrix for a global sequence alignment."""
    matrix = numpy.empty(shape=(str1.size+1, str2.size+1))
    matrix[0,0] = 0
    for i in xrange(1, matrix.shape[0]):
        matrix[i,0] = i*charmatrix.get(('', str1[i-1]), deletescore)
    for j in xrange(1, matrix.shape[1]):
        matrix[0,j] = j*charmatrix.get((str2[j-1], ''), insertscore)
    return matrix

def np_semi_global_matrix(str1, str2, substitutionscore, insertscore, deletescore,
                       charmatrix):
    """An initial matrix for a semi-global sequence alignment."""
    matrix = numpy.zeros(shape=(str1.size+1, str2.size+1))
    
    # We assume that str1 >= str2.
    # This is guaranteed by the semi_global_align function.
    for i in xrange(1, matrix.shape[0]):
        matrix[i,0] = i*charmatrix.get(('', str1[i-1]), deletescore)
    return matrix




def np_full_edit_distance(str1, str2, substitutionscore=1, insertscore=1,
                       deletescore=1, charmatrix={}, alignment_type='global'):
    """A modified implenmentation of the Wagner-Fischer algorithm using
    numpy. Unlike the minimal and optimized version in the
    "edit_distance" function, this returns the entire scoring matrix,
    and an operation matrix for backtracing and reconstructing the 
    edit operations. This should be used when an alignment is desired,
    not only the edit distance."""

    str1 = numpy.array(tuple(str1))
    str2 = numpy.array(tuple(str2))

    types = {'global': np_global_matrix, 'semi-global':np_semi_global_matrix}
    matrix = types[alignment_type](str1, str2, substitutionscore,
        insertscore, deletescore, charmatrix)

    steps = numpy.empty(shape=(str1.size+1, str2.size+1), dtype=numpy.object)
    steps[1:,0] = 'd'
    steps[0,1:] = 'i'
    steps[0,0] = ''
    for i in xrange(1, matrix.shape[0]):
        for j in xrange(1, matrix.shape[1]):
            c1 = str1[i-1]
            c2 = str2[j-1]

            scores = (('s', matrix[i-1, j-1] + charmatrix.get((c1, c2), substitutionscore)),
                      ('i', matrix[i, j-1] + charmatrix.get((c1, c2), insertscore)), 
                      ('d', matrix[i-1, j] + charmatrix.get((c1, c2), deletescore)))
            if str1[i-1] == str2[j-1]:
                matrix[i, j] = matrix[i-1, j-1]
                steps[i,j] = 'm'
            else:
                bestoption = min(scores, key=lambda x: x[1])
                matrix[i,j] = bestoption[1]
                steps[i,j] = bestoption[0]

    return matrix, steps

# ----------------------------------------------------------------------
# Language algorithms --------------------------------------------------
# ----------------------------------------------------------------------

# Useful unicode ranges
greek_coptic_range = (u'Greek Coptic', u'\u0370', u'\u03FF')
extended_greek_range = (u'Extended Greek', u'\u1F00', u'\u1FFF')
combining_diacritical_mark_range = (u'Combining Diacritical', u'\u0300', u'\u036f')

def unibarrier(func):
    """
    A decorator function; used to ensure that no str objects can be
    passed as either args or kwargs.
    """
    def unishielded(*args, **kwargs):
        for arg in args:
            if type(arg) == type(str('')):
                raise UnibarrierException(message='%s was a string!' % arg)
        for key, val in kwargs.iteritems():
            if type(val) == type(str('')):
                raise UnibarrierException(message='%s was a string!' % val)
        return func(*args, **kwargs)
    return unishielded


def uniblock(start, stop):
    """
    Return a range containing all the characters in the unicode table
    starting with 'start' (inclusive) and ending with end (inclusive).
    """
    ints = range(ord(start.decode('unicode-escape')),
                 ord(stop.decode('unicode-escape'))+1)

    return map(unichr, ints)  

def inblock(c, bounds):
    """
    Check that the character c is equal to or between the two bounding
    characters in the unicode table.
    """
    return ord(c) >= ord(bounds[0]) and ord(c) <= ord(bounds[1])

@unibarrier
def identify(string, unicode_blocks):
    """
    Determine percent-wise how many characters in the given string
    belong in each given unicode block. Ranges may be user defined, and
    not official unicode ranges. It is assumed that ranges do not
    overlap. unicode_blocks is an iterable of 3-tuples of the form
    (<name of block>, <first unichar in block>, <last unichar in the 
    block>).
    """
    result = {b[0]:0 for b in unicode_blocks}
    for c in string:
        for r in unicode_blocks:
            if inblock(c, (r[1], r[2])):
                result[r[0]] += 1

    return result


def unifilter(string, rangelist):
    filterset = []
    for block in rangelist:
        for i in unirange(block):
            filterset.append(unichar(i))
    return filter(filterset.__contains__, string)

def greek_chars():
    """
    Return a list containing all the characters from the Greek and
    Coptic, Extended Greek, and Combined Diacritical unicode blocks.
    """

    chars = [unichr(i) for i in unirange(greek_coptic_range)]
    for i in unirange(extended_greek_range):
        chars.append(unichr(i))
    for i in unirange(combining_diacritical_mark_range):
        chars.append(unichr(i))
    return chars

def greek_filter(string):
    """
    Remove all non-Greek characters from a string.
    """
    return filter(greek_chars().__contains__, string)


if __name__ == '__main__':
    path = os.path.expanduser('~/Desktop/tess/out.hocr.html')
    with open(path) as f:
        extract_bboxes(f)    

    #bbox+[0-9]+ [0-9]+ [0-9]+ [0-9]+

    # path = os.path.expanduser('~/Desktop/tess/out.hocr.html')
    # print path
    # with open(path) as f:
    #     tokens = extract_hocr_tokens(f)
    #     for t in tokens:
    #         print t


