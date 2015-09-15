# -*- coding: utf-8 -*-
"""
nidaba.algorithms.string
~~~~~~~~~~~~~~~~~~~~~~~~

Implementation of various algorithms operating on strings and unicode objects,
e.g. alignment, edit distances, and symmetric deletion searches.
"""

from __future__ import unicode_literals, print_function, absolute_import
from __future__ import division

import codecs
import numpy
import operator
import unicodedata
import itertools
import mmap
import math

from nidaba.nidabaexceptions import NidabaAlgorithmException

# ----------------------------------------------------------------------
# String and alignment algorithms --------------------------------------
# ----------------------------------------------------------------------


def sanitize(string, encoding=u'utf-8', normalization=u'NFD'):
    """
    Strip leading and trailing whitespace, convert to NFD. If the passed
    string is a str rather than an unicode, decode it with the specified
    encoding.
    """
    if isinstance(string, str):
        string = string.decode(encoding)

    return unicodedata.normalize(normalization, string.strip())


def strings_by_deletion(unistr, dels):
    """
    Compute the unique strings which can be formed from a string by
    deleting the specified number of characters from it. The results
    are sorted in ascending order.
    """
    new_words = set()
    for comb in itertools.combinations(range(len(unistr)), dels):
        new_words.add(u''.join((c for i, c in enumerate(unistr) if i not in
                                comb)))
    return sorted(list(new_words))


def sym_suggest(ustr, dic, delete_dic, depth, ret_count=0):
    """
    Return a list of "spelling" corrections using a symmetric deletion search.
    Dic is a set of correct words. Delete_dic is of the form
    {edit_term:[(candidate1, edit_distance), (candidate2, edit_distance),
    ...]}.
    """
    suggestions = set()
    dels = strings_by_deletion(ustr, depth)
    if ustr in dic:
        suggestions.add(ustr)

    if ustr in delete_dic:  # ustr is missing characters.
        suggestions = suggestions.union(set(delete_dic[ustr]))
    for s in dels:
        if s in dic:    # ustr has extra characters.
            suggestions.add(s)
        if s in delete_dic:  # ustr has substitutions of twiddles
            suggestions = suggestions.union(set(delete_dic[s]))

    return list(suggestions if ret_count <= 0 else suggestions[:ret_count])


def parse_del_dict_entry(entry):
    return [] if entry is None else [word.strip()
                                     for word in entry.split(u' ')]


def suggestions(ustr, sugs, freq=None):
    """
    Call mapped_sym_suggest, and return the suggestions as a
    sorted list. Python's built in sort is stable, so we can
    simply sort repeatedly, from least important aspect to
    most important.
    """
    sugs = sorted(sugs)  # Alphabetic sort
    if freq is not None:
        sugs = sorted(sorted(sugs), key=lambda x: freq[x])  # By frequency
    # By edit distance
    sugs = sorted(sugs, key=lambda x: edit_distance(ustr, x))

    return sugs


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
    ustr_entry = mmap_bin_search(ustr, del_dic_path)
    word_for_ustr = parse_del_dict_entry(ustr_entry)
    if word_for_ustr is not None:
        # get the words reachable by adding to ustr.
        inserts = set(w for w in word_for_ustr)
    for s in dels:
        if s in dic:
            deletes.add(s)  # Add a word reachable by deleting from ustr.

        line_for_s = parse_del_dict_entry(mmap_bin_search(s, del_dic_path))
        if line_for_s is not None:
            # Get the words reachable by deleting from originals, adding to
            # them. Note that this is NOT the same as 'Levenshtein'
            # substitution.
            for sug in line_for_s:
                distance = edit_distance(sug, ustr)
                if distance == depth:
                    subs.add(sug)
                elif distance > depth:
                    int_and_dels.add(sug)

    return {u'dels': deletes, u'ins': inserts,
            u'subs': subs, u'ins+dels': int_and_dels}


def prev_newline(mm, line_buffer_size=100):
    """
    Return the pointer position immediately after the closest left hand
    newline, or to the beginning of the file if no such newlines exist.
    """
    # mm.seek(mm.tell - line_buffer_size)
    # TODO this fails on a line greater than line_buffer_size in length
    return mm.rfind(u'\n', mm.tell() - line_buffer_size, mm.tell()) + 1


def compare_strings(u1, u2):
    if u1 == u2:
        return 0
    elif u1 < u2:
        return 1
    else:
        return -1


def todec(ustr):
    uthex = u''
    for cp in ustr:
        uthex += u'<' + cp + u'>' + u',' + unicode(ord(cp)) + u':'
    return uthex.encode('utf-8')


def truestring(unicode):
    out = u'<' + u':'.join([u for u in unicode]) + u'>'
    return out

# ----------------------------------------------------------------------
# Binary search dictionary entry parsers -------------------------------
# ----------------------------------------------------------------------


def key_for_del_dict_entry(entry):
    """
    Parse a line from a symmetric delete dictionary.
    Returns a tuple of the form (key, list of values).
    """
    key, val = entry.split(u'\t')
    return (key, val.strip())


def key_for_single_word(entry):
    """
    Parse a line from a simple "one word per line" dictionary.
    """
    cleanword = entry.strip()
    return (cleanword, cleanword)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------


# TODO Implement doubling-length backward search to make line_buffer_size
# irrelevant.

def mmap_bin_search(ustr, dictionary_path,
                    entryparser_fn=key_for_del_dict_entry,
                    line_buffer_size=200):
    """
    Perform a binary search on a memory mapped dictionary file, and
    return the parsed entry, or None if the specified entry cannot be
    found. This function assumes that the dictionary is properly
    formatted and well-formed, otherwise the behavior is undefined.
    Line buffer must not be shorter than the longest line in the
    dictionary. Entries may be any strings which do not contain newlines
    (newlines delimint entries); the entryparser_fn should be of the
    form fn_name(unicodestr), decorated with @unibarrier and return a
    tuple of the form (keytosort by, val). By default, it uses the
    function for parsing symmetric deletion dictionary entries.
    The line_buffer_size argument must be >= the longest line in the
    dictionary, or behavior is undefined.
    """

    def current_entry(mm):
        start = mm.tell()
        rawline = mm.readline()
        mm.seek(start)
        return entryparser_fn(rawline.decode(u'utf-8'))

    with codecs.open(dictionary_path, 'r+b') as f:
        # memory-map the file, size 0 means whole file
        mm = mmap.mmap(f.fileno(), 0)
        imin = 0
        imax = mm.size()
        count = 0
        while True:
            mid = imin + int(math.floor((imax - imin) / 2))
            mm.seek(mid)
            mm.seek(prev_newline(mm))
            key, entry = current_entry(mm)

            if key == ustr:
                return entry
            elif key < ustr:
                imin = mid + 1
            else:
                imax = mid - 1

            count += 1
            if imin >= imax:
                break
        return None

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------


def initmatrix(rows, columns, defaultval=0):
    """Initializes a 2d list to the desired dimensions."""
    return [[defaultval for j in xrange(columns)] for i in xrange(rows)]


def mr(matrix):
    """Returns a string rep of a 2d list as a matrix. Useful for
    debugging."""
    if matrix == []:
        return '[]'
    string = '['
    count = 0
    for row in matrix:
        if count >= 1:
            string += ' '
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
    i, j = start if start is not None else (
        len(matrix) - 1, len(matrix[0]) - 1)
    key = {'i': (0, -1), 'd': (-1, 0), 'm': (-1, -1), 's': (-1, -1)}
    path = []

    while matrix[i][j] != '':
        path.insert(0, matrix[i][j])
        i, j = tuple(map(operator.add, (i, j), key[matrix[i][j]]))

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
        raise NidabaAlgorithmException('shortseq must be <= longseq in\
                                       length!')

    matrix, steps = native_full_edit_distance(shortseq, longseq,
                                              substitutionscore=substitutionscore,
                                              insertscore=insertscore,
                                              deletescore=deletescore,
                                              charmatrix=charmatrix,
                                              alignment_type='semi-global')
    return native_backtrace(
        steps, start=(len(matrix) - 1, matrix[-1].index(min(matrix[-1]))))


def native_global_matrix(str1, str2, substitutionscore, insertscore,
                         deletescore, charmatrix):
    """An initial matrix for a global sequence alignment."""
    matrix = initmatrix(len(str1) + 1, len(str2) + 1)
    for i in xrange(1, len(matrix)):
        matrix[i][0] = i * charmatrix.get(('', str1[i - 1]), deletescore)
    for j in xrange(1, len(matrix[0])):
        matrix[0][j] = j * charmatrix.get((str2[j - 1], ''), insertscore)
    return matrix


def native_semi_global_matrix(str1, str2, substitutionscore, insertscore,
                              deletescore, charmatrix):
    matrix = initmatrix(len(str1) + 1, len(str2) + 1)
    for i in xrange(1, len(matrix)):
        matrix[i][0] = i * charmatrix.get(('', str1[i - 1]), deletescore)
    return matrix


def native_full_edit_distance(str1, str2, substitutionscore=1, insertscore=1,
                              deletescore=1, charmatrix={},
                              alignment_type='global'):

    matrix, steps = full_edit_distance(str1, str2,
                                       substitutionscore=substitutionscore,
                                       insertscore=insertscore,
                                       deletescore=deletescore,
                                       charmatrix=charmatrix,
                                       alignment_type=alignment_type)
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
    return m[-1][-1]


def full_edit_distance(str1, str2, substitutionscore=1, insertscore=1,
                       deletescore=1, ins_func=None, iargs=[], ikwargs={},
                       del_func=None, dargs=[], dkwargs={}, sub_func=None,
                       sargs=[], skwargs={}, charmatrix={},
                       alignment_type='global'):
    """
    A version of the modified Wagner-Fischer algorithm that accepts user
    defined scoreing functions. These functions should be of the form
    fname(token1, token2, args*, kwargs**) and return an integer
    >= 0. A return value of 0 indicates an optimality. The larger, the
    integer, the worse the score. Charmatrix is here only used to
    calulate default delete and insert scores for the initial matrix.
    """

    def dscore(c1, c2, default):
        return charmatrix.get((c1, c2), default)
    if ins_func is None:
        ins_func = dscore
        iargs = [insertscore]
    if del_func is None:
        del_func = dscore
        dargs = [deletescore]
    if sub_func is None:
        sub_func = dscore
        sargs = [substitutionscore]

    types = {'global': native_global_matrix,
             'semi-global': native_semi_global_matrix}
    matrix = types[alignment_type](str1, str2, substitutionscore, insertscore,
                                   deletescore, charmatrix)

    steps = initmatrix(len(str1) + 1, len(str2) + 1, defaultval='')
    steps[0][1:] = list('i' * (len(str2)))
    for idx in xrange(1, len(matrix)):
        steps[idx][0] = 'd'
    for i in xrange(1, len(matrix)):
        for j in xrange(1, len(matrix[0])):
            c1 = str1[i - 1]
            c2 = str2[j - 1]

            scores = (('s', matrix[i - 1][j - 1] + sub_func(c1, c2, *sargs,
                                                            **skwargs)),
                      ('i', matrix[i][j - 1] + ins_func(c1, c2, *iargs,
                                                        **ikwargs)),
                      ('d', matrix[i - 1][j] + del_func(c1, c2, *dargs,
                                                        **dkwargs)))
            if str1[i - 1] == str2[j - 1]:
                matrix[i][j] = matrix[i - 1][j - 1]
                steps[i][j] = 'm'
            else:
                bestoption = min(scores, key=lambda x: x[1])
                matrix[i][j] = bestoption[1]
                steps[i][j] = bestoption[0]

    return matrix, steps

# ----------------------------------------------------------------------
# String and alignment algorithms (numpy versions) ---------------------
# ----------------------------------------------------------------------


def np_backtrace(matrix, start=None):
    """Trace edit steps backward to find an edit sequence for an
    alignment. Starts at the provided 'start' index, or in the i,j'th
    index if none is provided. The backtrace always ends
    at the index 0,0."""

    i, j = start if start is not None else (
        matrix.shape[0] - 1, matrix.shape[1] - 1)
    key = {'i': (0, -1), 'd': (-1, 0), 'm': (-1, -1), 's': (-1, -1)}
    path = []

    while matrix[i, j] != '':
        path.insert(0, matrix[i, j])
        i, j = tuple(map(operator.add, (i, j), key[matrix[i, j]]))

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
        raise NidabaAlgorithmException('shortseq must be <= longseq in\
                                       length!')

    matrix, steps = np_full_edit_distance(shortseq, longseq,
                                          substitutionscore=substitutionscore,
                                          insertscore=insertscore,
                                          deletescore=deletescore,
                                          charmatrix=charmatrix,
                                          alignment_type='semi-global')
    back = np_backtrace(steps, start=(matrix.shape[0] - 1,
                                      numpy.argmin(matrix[-1:])))
    return back


def np_global_matrix(str1, str2, substitutionscore, insertscore, deletescore,
                     charmatrix):
    """An initial matrix for a global sequence alignment."""
    matrix = numpy.empty(shape=(str1.size + 1, str2.size + 1))
    matrix[0, 0] = 0
    for i in xrange(1, matrix.shape[0]):
        matrix[i, 0] = i * charmatrix.get(('', str1[i - 1]), deletescore)
    for j in xrange(1, matrix.shape[1]):
        matrix[0, j] = j * charmatrix.get((str2[j - 1], ''), insertscore)
    return matrix


def np_semi_global_matrix(str1, str2, substitutionscore, insertscore,
                          deletescore, charmatrix):
    """An initial matrix for a semi-global sequence alignment."""
    matrix = numpy.zeros(shape=(str1.size + 1, str2.size + 1))

    # We assume that str1 >= str2.
    # This is guaranteed by the semi_global_align function.
    for i in xrange(1, matrix.shape[0]):
        matrix[i, 0] = i * charmatrix.get(('', str1[i - 1]), deletescore)
    return matrix


def np_full_edit_distance(str1, str2, substitutionscore=1, insertscore=1,
                          deletescore=1, charmatrix={},
                          alignment_type='global'):
    """A modified implenmentation of the Wagner-Fischer algorithm using
    numpy. Unlike the minimal and optimized version in the
    "edit_distance" function, this returns the entire scoring matrix,
    and an operation matrix for backtracing and reconstructing the
    edit operations. This should be used when an alignment is desired,
    not only the edit distance."""

    str1 = numpy.array(tuple(str1))
    str2 = numpy.array(tuple(str2))

    types = {'global': np_global_matrix, 'semi-global': np_semi_global_matrix}
    matrix = types[alignment_type](str1, str2, substitutionscore,
                                   insertscore, deletescore, charmatrix)

    steps = numpy.empty(
        shape=(str1.size + 1, str2.size + 1), dtype=numpy.object)
    steps[1:, 0] = 'd'
    steps[0, 1:] = 'i'
    steps[0, 0] = ''
    for i in xrange(1, matrix.shape[0]):
        for j in xrange(1, matrix.shape[1]):
            c1 = str1[i - 1]
            c2 = str2[j - 1]

            scores = (('s', matrix[i - 1, j - 1] + charmatrix.get((c1, c2),
                                                                  substitutionscore)),
                      ('i', matrix[i, j - 1] + charmatrix.get((c1, c2),
                                                              insertscore)),
                      ('d', matrix[i - 1, j] + charmatrix.get((c1, c2),
                                                              deletescore)))
            if str1[i - 1] == str2[j - 1]:
                matrix[i, j] = matrix[i - 1, j - 1]
                steps[i, j] = 'm'
            else:
                bestoption = min(scores, key=lambda x: x[1])
                matrix[i, j] = bestoption[1]
                steps[i, j] = bestoption[0]

    return matrix, steps

# ----------------------------------------------------------------------
# Language algorithms --------------------------------------------------
# ----------------------------------------------------------------------

# Useful unicode rang
ascii_range = (u'Ascii', unichr(0), unichr(127))
greek_coptic_range = (u'Greek Coptic', u'\u0370', u'\u03FF')
extended_greek_range = (u'Extended Greek', u'\u1F00', u'\u1FFF')
combining_diacritical_mark_range = (
    u'Combining Diacritical', u'\u0300', u'\u036f')

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
    ints = range(ord(start), ord(stop) + 1)

    return map(unichr, ints)


def inblock(c, bounds):
    """
    Check that the character c is equal to or between the two bounding
    characters in the unicode table.
    """
    return ord(c) >= ord(bounds[0]) and ord(c) <= ord(bounds[1])


def identify(string, unicode_blocks):
    """
    Determine percent-wise how many characters in the given string
    belong in each given unicode block. Ranges may be user defined, and
    not official unicode ranges. It is assumed that ranges do not
    overlap. unicode_blocks is an iterable of 3-tuples of the form
    (<name of block>, <first unichar in block>, <last unichar in the
    block>).
    """
    result = {b[0]: 0 for b in unicode_blocks}
    for c in string:
        for r in unicode_blocks:
            if inblock(c, (r[1], r[2])):
                result[r[0]] += 1

    return result


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

    return inlang / len(unistr) >= threshold


def isgreek(ustr):
    return islang(ustr, [greek_coptic_range, extended_greek_diacritics,
                         greek_and_coptic_diacritics])


def greek_chars():
    """
    Return a list containing all the characters from the Greek and
    Coptic, Extended Greek, and Combined Diacritical unicode blocks.
    """

    chars = uniblock(greek_coptic_range[1], greek_coptic_range[2])
    chars += uniblock(extended_greek_range[1], extended_greek_range[2])
    chars += uniblock(combining_diacritical_mark_range[1],
                      combining_diacritical_mark_range[2])
    return chars


def greek_filter(string):
    """
    Remove all non-Greek characters from a string.
    """
    return filter(greek_chars().__contains__, string)


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
        if i != len(l) - 1:
            result += u', '
    result += u']'
    return result.encode(encoding)
