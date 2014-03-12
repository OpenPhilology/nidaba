# -*- coding: utf-8 -*-
import os
import numpy
import codecs
import operator
from kitchen.text.converters import to_unicode, to_bytes

from lxml import etree


# ------------------------------------------------------------------------------------------
# Exceptions -------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------

class AlgorithmException(Exception):
    """A simple exception for algorithm specific errors."""
    def __init__(self, message=None):
        Exception.__init__(self, message)
        



# ------------------------------------------------------------------------------------------
# String and alignment algorithms ----------------------------------------------------------
# ------------------------------------------------------------------------------------------

def edit_distance(str1, str2):
    """Calculate the Levenshtein or edit distance between two strings, tuples, or lists.
    Types can be mixed (e.g. compare a string to a list of strings) """
    if len(str1) < len(str2):
        return edit_distance(str2, str1)
 
    # So now we have len(str1) >= len(str2).
    if len(str2) == 0:
        return len(str1)
 
    # We call tuple() to force strings to be used as sequences
    # ('c', 'a', 't', 's') - numpy uses them as values by default.
    str1 = numpy.array(tuple(str1))
    str2 = numpy.array(tuple(str2))
 
    # We use a dynamic programming algorithm, but with the
    # added optimization that we only need the last two rows
    # of the matrix.
    previous_row = numpy.arange(str2.size + 1)
    for s in str1:
        # Insertion (str2 grows longer than str1):
        current_row = previous_row + 1 # Adds one at every index.

        # Substitution or matching:
        # str2 and str1 items are aligned, and either
        # are different (cost of 1), or are the same (cost of 0).

        current_row[1:] = numpy.minimum(
                current_row[1:],
                numpy.add(previous_row[:-1], str2 != s))
        # Deletion (str2 grows shorter than str1):
        current_row[1:] = numpy.minimum(
                current_row[1:],
                current_row[0:-1] + 1)
 
        previous_row = current_row
 
    return previous_row[-1]



def backtrace(matrix, start=None):
    """Trace edit steps backward to find an edit sequence for an alignment.
    Starts at the provided 'start' index, or in the i,j'th index if none is provided.
    The backtrace always ends at the index 0,0."""

    i,j = start if start is not None else (matrix.shape[0]-1, matrix.shape[1]-1)
    key = {'i':(0,-1), 'd':(-1,0), 'm':(-1,-1), 's':(-1, -1)}
    path = []

    while matrix[i,j] != '':
        path.insert(0, matrix[i,j])
        i,j = tuple(map(operator.add, (i,j), key[matrix[i,j]]))

    return path

def align(str1, str2, substitutionscore=1, insertscore=1, deletescore=1, charmatrix={}):
    """Calculate the edit distance of two strings, then backtrace to find a valid edit sequence."""
    matrix, steps = full_edit_distance(str1, str2, substitutionscore=substitutionscore,  insertscore=insertscore, deletescore=deletescore, charmatrix=charmatrix)
    return backtrace(steps)

def semi_global_align(shortseq, longseq, substitutionscore=1, insertscore=1, deletescore=1, charmatrix={}):
    """Find a semi-global alignment between two strings."""
    if len(shortseq) > len(longseq):
        raise AlgorithmException('shortseq must be <= longseq in length!')

    # short, longseq = sorted((str1, str2), key=lambda x: len(x))
    matrix, steps = full_edit_distance(shortseq, longseq, substitutionscore=substitutionscore, insertscore=insertscore, deletescore=deletescore, charmatrix=charmatrix, alignment_type='semi-global')
    back = backtrace(steps, start=(matrix.shape[0]-1, numpy.argmin(matrix[-1:])))
    return back

# def local_align(str1, str2, substitutionscore=1, insertscore=1, deletescore=1, charmatrix={}):

def global_matrix(str1, str2, substitutionscore, insertscore, deletescore, charmatrix):
    """An initial matrix for a global sequence alignment."""
    matrix = numpy.empty(shape=(str1.size+1, str2.size+1))
    matrix[0,0] = 0
    for i in xrange(1, matrix.shape[0]):
        matrix[i,0] = i*charmatrix.get(('', str1[i-1]), deletescore)
    for j in xrange(1, matrix.shape[1]):
        matrix[0,j] = j*charmatrix.get((str2[j-1], ''), insertscore)
    return matrix

def semi_global_matrix(str1, str2, substitutionscore, insertscore, deletescore, charmatrix):
    """An initial matrix for a semi-global sequence alignment."""
    matrix = numpy.zeros(shape=(str1.size+1, str2.size+1))
    for i in xrange(1, matrix.shape[0]): # We assume that str1 >= str2. This is guaranteed by the semi_global_align function.
        matrix[i,0] = i*charmatrix.get(('', str1[i-1]), deletescore)
    return matrix

# def local_matrix(str1, str2, substitutionscore, insertscore, deletescore, charmatrix):
#     """An initial matrix for a local sequence alignment."""
#     matrix = numpy.empty(shape=(str1.size+1, str2.size+1))
#     matrix[1:,0] = 0
#     matrix[0,1:] = 0
#     return matrix

def full_edit_distance(str1, str2, substitutionscore=1, insertscore=1, deletescore=1, charmatrix={}, alignment_type='global'):
    """A modified implenmentation of the Wagner-Fischer algorithm using numpy. Unlike the minimal and optimized version in the
    "edit_distance" function, this returns the entire scoring matrix, and an operation matrix for backtracing and reconstructing the 
    edit operations. This should be used when an alignment is desired, not only the edit distance."""

    str1 = numpy.array(tuple(str1))
    str2 = numpy.array(tuple(str2))

    types = {'global': global_matrix, 'semi-global':semi_global_matrix}
    matrix = types[alignment_type](str1, str2, substitutionscore, insertscore, deletescore, charmatrix)

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

# ------------------------------------------------------------------------------------------
# Greek algorithms -------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------

def greek_and_coptic_range():
    """Return a range representing the Greek and Coptic unicode block."""
    return range(ord('\u0370'.decode('unicode-escape')), ord('\u03FF'.decode('unicode-escape'))+1)

def extended_greek_range():
    """Return a range representing the Extended Greek unicode block."""
    return range(ord('\u1F00'.decode('unicode-escape')), ord('\u1FFF'.decode('unicode-escape'))+1)

def combining_diacritical_mark_range():
    """Return a range representing the Combined Diacritical Mark unicode block."""
    return range(ord('\u0300'.decode('unicode-escape')), ord('\u0360'.decode('unicode-escape'))+1)

def greek_chars():
    """Return a list containing all the characters from the Greek and Coptic, Extended Greek, and Combined Diacritical unicode blocks."""
    chars = [unichr(i) for i in greek_and_coptic_range()]
    for i in extended_greek_range():
        chars.append(unichr(i))
    for i in combining_diacritical_mark_range():
        chars.append(unichr(i))
    return chars

def greek_filter(string):
    """Remove all non-Greek characters from a string."""
    return filter(greek_chars().__contains__, string)

# ------------------------------------------------------------------------------------------
# hOCR algorithms --------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------

def extract_hocr_tokens(hocr_file):
    """Extracts all the nonempty words in an hOCR file and returns them as a list."""
    words = []
    context = etree.iterparse(hocr_file, events=('end',), tag='span', html=True)
    for event, element in context:
        word = to_unicode(element.text.rstrip()) # Strip extraneous newlines generated by the ocr_line span tags.
        if len(word) > 0:
            words.append(word)
        element.clear()
        while element.getprevious() is not None:
            del element.getparent()[0]
    del context
    return words

# if __name__ == '__main__':




