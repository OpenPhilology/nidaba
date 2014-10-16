# -*- coding: utf-8 -*-
from __future__ import division
import os
import re
import numpy
import codecs
import operator
import time
import unicodedata
import itertools
import codecs
import string
import mmap
import linecache
import timeit
import subprocess
import math
import tempfile
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

def sanitize(string, encoding=u'utf-8', normalization=u'NFD'):
    """
    Strip leading and trailing whitespace, convert to NFD. If the passed
    string is a str rather than an unicode, decode it with the specified
    encoding.
    """
    if type(string) == type(''):
        string = string.decode(encoding)

    return unicodedata.normalize(normalization, string.strip())

@unibarrier
def strings_by_deletion(unistr, dels):
    """
    Compute the unique strings which can be formed from a string by
    deleting the specified number of characters from it. The results
    are sorted in ascending order.
    """
    new_words = set()
    for comb in itertools.combinations(range(len(unistr)), dels):
        new_words.add(u''.join((c for i, c in enumerate(unistr) if i not in comb)))
    return sorted(list(new_words))

@unibarrier
def parse_sym_entry(entry):
    """
    Parse a line from a symmetric delete dictionary into a python data
    structure. Returns a tuple of the form (key, list of values).
    """
    key, words = entry.split(u' : ')
    return (key, [word.strip() for word in words.split(u' ')])

def load_sym_dict(path):
    path = os.path.abspath(os.path.expanduser(path))
    dic = {}
    with codecs.open(path, encoding='utf-8') as dfile:
        for line in dfile:
            word, dels = line.split(u' : ')
            dic[word] = [s.strip(u'\n') for s in dels.split(u' ')]

    return dic

@unibarrier
def sym_suggest(ustr, dic, delete_dic, depth, ret_count=0):
    """
    Return a list of "spelling" corrections using a symmetric deletion
    search. Dic is a set of correct words. Delete_dic is of the form
    {edit_term:[(candidate1, edit_distance), (candidate2, edit_distance), ...]}.
    """
    suggestions = set()
    dels = strings_by_deletion(ustr, depth)
    if ustr in dic:
        suggestions.add(ustr)

    if ustr in delete_dic: # ustr is missing characters.
        suggestions = suggestions.union(set(delete_dic[ustr]))
    for s in dels:
        if s in dic:    # ustr has extra characters.
            suggestions.add(s)
        if s in delete_dic: #ustr has substitutions of twiddles
            suggestions = suggestions.union(set(delete_dic[s]))

    return list(suggestions if ret_count <= 0 else suggestions[:ret_count])

@unibarrier
def mapped_sym_suggest(ustr, del_dic_path, dic, depth, ret_count=0):
    """
    Generate a list of spelling suggestions using the memory mapped
    dictionary search/symmetric delete algorithm. Return only
    suggestions at the specified depth, not up to and including that
    depth.
    """
    deletes = set()
    inserts = set()
    int_and_dels = set()
    subs = set()

    dels = strings_by_deletion(ustr, depth)
    line_for_ustr = deldict_bin_search(ustr, del_dic_path)
    if line_for_ustr is not None:
        inserts = set(w for w in line_for_ustr[1])  # get the words reachable by adding to ustr.
    for s in dels:
        if s in dic:
            deletes.add(s) # Add a word reachable by deleting from ustr.

        line_for_s = deldict_bin_search(s, del_dic_path)
        if line_for_s is not None:
            # Get the words reachable by deleting from originals, adding to them.
            # Note that this is NOT the same as 'Levehsein' substitution.
            for sug in line_for_s[1]:
                distance = edit_distance(sug, ustr)
                if distance == depth:
                    subs.add(sug)
                elif distance > depth:
                    int_and_dels.add(sug)
                else:   #Only possible if ustr is in the dictionary; hence distance == 0.
                    pass

    return {u'dels':deletes, u'ins':inserts, u'subs':subs, u'ins+dels':int_and_dels}

@unibarrier
def edits1(ustr, alphabet):
   splits     = [(ustr[:i], ustr[i:]) for i in range(len(ustr) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
   inserts    = [a + c + b for a, b in splits for c in alphabet]
   return set(deletes + transposes + replaces + inserts)

@unibarrier
def edits2(ustr, alphabet, dictionary):
    return set(e2 for e1 in edits1(ustr, alphabet) for e2 in edits1(e1, alphabet) if e2 in dictionary)

def known(words, dictionary):
    return list(w for w in words if w in dictionary)

@unibarrier
def suggest(ustr, alphabet, dictionary):
    suggestions = []
    if ustr in dictionary:
        suggestions.append(ustr)
    suggestions.append(known(edits1(ustr) + edits2(ustr, alphabet, dictionary)))


def load_lines(path, encoding='utf-8'):
    with codecs.open(path, 'r', encoding) as f:
        return [line for line in f]

def count_lines(path):
    """
    Get the number of lines in a file by counting the newlines.
    Use a call to wc so that extremely large files can be processed
    quickly.
    """
    cmd = [u'wc', u'-l', path]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)

    out, err = p.communicate()
    return float(out.split(u' ', 1)[0])


def prev_newline(mm, line_buffer_size=100):
    """
    Return the pointer position immediately after the closest left hand
    newline, or to the beginning of the file if no such newlines exist.
    """
    # mm.seek(mm.tell - line_buffer_size)
    # TODO this fails on a line greater than line_buffer_size in length
    return mm.rfind(u'\n', mm.tell() - line_buffer_size, mm.tell()) + 1


@unibarrier
def compare_strings(u1, u2):
    if u1 == u2:
        return 0
    elif u1 < u2:
        return 1
    else:
        return -1

@unibarrier
def todec(ustr):
    uthex = u''
    for cp in ustr:
        uthex += u'<' + cp + u'>' + u',' + unicode(ord(cp)) + u':'
    return uthex.encode('utf-8')


@unibarrier
def truestring(unicode):
    out = u'<' + u':'.join([u for u in unicode]) + u'>'
    return out

# TODO Implement doubling-length backward search to make line_buffer_size
# irrelevant.
@unibarrier
def deldict_bin_search(ustr, dictionary_path, line_buffer_size=200):
    """
    Perform a binary search on a memory mapped dictionary file, and
    return the parsed entry, or None if the specified entry cannot be
    found. This function assumes that the dictionary is properly
    formatted and well-formed, otherwise the behavior is undefined.
    Line buffer must not be shorter than the longest line in the
    dictionary.
    """

    def current_key(mm):
        start = mm.tell()
        rawline = mm.readline()
        mm.seek(start)
        return parse_sym_entry(rawline.decode(u'utf-8'))

    with codecs.open(dictionary_path, 'r+b') as f:
        # memory-map the file, size 0 means whole file
        mm = mmap.mmap(f.fileno(), 0)
        imin = 0
        imax = mm.size()
        count = 0
        while True:
            mid = imin + int(math.floor((imax - imin)/2))
            mm.seek(mid)
            mm.seek(prev_newline(mm))
            parsedline = current_key(mm)
            key = parsedline[0]

            if key == ustr:
                return parsedline
            elif key < ustr:
                imin = mid + 1
            else:
                imax = mid - 1

            count += 1
            if imin >= imax:
                break
        return None

def load_del_dic(path, encoding='utf-8'):
    # mfd = os.open(path, os.O_RDONLY)
    # data = mmap.mmap(mfd, 0, prot=mmap.PROT_READ)
    with codecs.open(path, 'r+b') as f:
        # memory-map the file, size 0 means whole file
        mm = mmap.mmap(f.fileno(), 0)
        lines = 6
        words = []
        for i in xrange(0,6):
            print mm.readline()
            print mm.tell()
            # next_line = mm.find(u'\n')
            # words.append(mm[mm.tell():next_line].decode('utf-8'))
            # print words[i].encode('utf-8')
            # mm.seek(next_line + 1)
        # print mm.tell()
        # print mm[mm.tell():mm.find(u'\n')]
        # print mm[mm.tell():mm.find(u'\n')]







        # print data.decode('utf-8'), type(data.decode('utf-8'))
        # print 'line is <%s>' % mm.readline().strip().decode('utf-8')
        # print 'line is <%s>' % mm.readline().strip().decode('utf-8')

        # t = mm.readline()
        # print t, type(t)
        # print t.decode('utf-8').encode('utf-8')

        # print mm.readline().strip()
        # print mm.readline().strip()
        # print mm.readline().strip()





        # read content via standard file methods
        # print mm.readline()  # prints "Hello Python!"
        # read content via slice notation
        # print mm[:5]  # prints "Hello"
        # for i in xrange(0,50):
        #     print mm[i]
        # update content using slice notation;
        # note that new content must have same size
        # mm[6:] = " world!\n"
        # ... and read again using standard file methods
        # mm.seek(0)
        # print mm.readline()  # prints "Hello  world!"
        # close the map
        mm.close()

# def set_pointer_to_prev(mm):


# @unibarrier
# def get_entry(mm, ustr):


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
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

# Useful unicode rang
ascii_range = (u'Ascii', unichr(0), unichr(127))
greek_coptic_range = (u'Greek Coptic', u'\u0370', u'\u03FF')
extended_greek_range = (u'Extended Greek', u'\u1F00', u'\u1FFF')
combining_diacritical_mark_range = (u'Combining Diacritical', u'\u0300', u'\u036f')

# This is a list of all tone mark code points not in the combining
# diacritial block. They are from the "Greek and Coptic" and "Extended
# Greek" blocks.
greek_and_coptic_diacritics = [u'\u037A', u'\u0384', u'\u0385']
extended_greek_diacritics = [u'\u1fbd', u'\u1fbe', u'\u1fbf', u'\u1fc0',
                             u'\u1fc1', u'\u1fcd', u'\u1fce', u'\u1fcf',
                             u'\u1fdd', u'\u1fde', u'\u1fdf', u'\u1fed',
                             u'\u1fee', u'\u1fef', u'\u1ffd', u'\u1ffe']

def uniblock(start, stop):
    """
    Return a list containing all the characters in the unicode table
    starting with 'start' (inclusive) and ending with end (inclusive).
    """
    ints = range(ord(start), ord(stop)+1)

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

@unibarrier
def islang(unistr, unicode_blocks, threshold=1.0):
    """
    Determine if a given (unicode) string belongs to a certain langauge.
    This calls the identify function to determine what fraction of the
    string's characters are in the specified blocks. It returns true if
    the number of chars in those blocks is >= threshold.
    Threshold is a float between 0 and 1.
    """
    if threshold > 1.0 or threshold <= 0.0:
        raise Exception(u'Threshold must be > 0.0 and <= 1.0')

    res = identify(unistr, unicode_blocks)
    inlang = 0
    for block in unicode_blocks:
        inlang += res[block[0]]

    return inlang/len(unistr) >= threshold

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

    chars = uniblock(greek_coptic_range[1], greek_coptic_range[2])
    chars += uniblock(extended_greek_range[1], extended_greek_range[2])
    chars += uniblock(combining_diacritical_mark_range[1], combining_diacritical_mark_range[2])
    return chars

def greek_filter(string):
    """
    Remove all non-Greek characters from a string.
    """
    return filter(greek_chars().__contains__, string)

@unibarrier
def strip_diacritics(ustr):
    """
    Remove all Greek diacritics from the specified string. Expects the
    string to be in NFD.
    """
    diacritics = uniblock(combining_diacritical_mark_range[1],
                          combining_diacritical_mark_range[2])
    diacritics += greek_and_coptic_diacritics + extended_greek_diacritics
    return u''.join(c for c in ustr if c not in diacritics)

def list_to_uni(l, encoding=u'utf-8'):
    """
    Return a human readable string representation of a list of unicode
    strings using the specified encoding.
    """
    result = u'['
    for i in xrange(0, len(l)):
        result += l[i]
        if i != len(l) - 1: result += u', '
    result += u']'
    return result.encode(encoding)

# if __name__ == '__main__':






