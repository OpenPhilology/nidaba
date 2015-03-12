# -*- coding: utf-8 -*-
# This module contains functions for dealing with words and dictionaries,
# such as extracting words from texts, normalizing encodings, building
# symmetric deletion dictionaries, etc.

from __future__ import absolute_import

import os
import codecs
import glob
import nidaba.algorithms as alg
from collections import Counter


@alg.unibarrier
def cleanlines(path, encoding=u'utf-8', normalization=u'NFD'):
    """
    Read in lines from a file and return them as a sanitized list.
    Non-unique linse will be repeated.
    """
    words = []
    with codecs.open(path, u'r', encoding=encoding) as lines:
        for line in lines:
            words.append(alg.sanitize(line, normalization=normalization))
    return words


@alg.unibarrier
def cleanwords(path, encoding=u'utf-8', normalization=u'NFD'):
    """
    Read in every word from a files as separated by lines and spaces.
    Non-unique words will be repeated as they are read in.
    """
    words = []
    with codecs.open(path, u'r', encoding=encoding) as lines:
        for line in lines:
            for seg in line.split(u' '):
                clean = alg.sanitize(seg, normalization=normalization)
                if clean != u'':
                    words.append(clean)
    return words


@alg.unibarrier
def uniquewords_with_freq(path, encoding=u'utf-8', normalization=u'NFD'):
    """
    Read in every word from a file as separated by lines and spaces.
    Return a counter (behaves like a dictionary) of unique words
    along with the number of times they occurred.
    """
    words = cleanwords(path, encoding=encoding, normalization=normalization)
    freq = Counter(words)
    return freq


@alg.unibarrier
def cleanuniquewords(path, encoding=u'utf-8', normalization=u'NFD'):
    """
    Read in lines from a file as separated by lines and spaces,
    convert them to the specified normalization, andreturn a list
    of all unique words.
    """
    return set(
        cleanwords(path, encoding=encoding, normalization=normalization))


@alg.unibarrier
def words_from_files(dirpath, encoding=u'utf-8', normalization=u'NFD'):
    """
    Create a dictionary from a directory of text files.
        All file in the given directory will be parsed.
    """
    words = []
    for filename in filter(os.path.isfile, glob.glob(dirpath + '/*')):
        words += cleanwords(filename, encoding=encoding,
                            normalization=normalization)
    return words


@alg.unibarrier
def unique_words_from_files(dirpath, encoding=u'utf-8', normalization=u'NFD'):
    """
    Create a set of unique words from a directory of text files.
    All file in the given directory will be parsed.
    """
    return set(
        words_from_files(dirpath, encoding=encoding,
                         normalization=normalization))


@alg.unibarrier
def make_dict(outpath, iterable, encoding=u'utf-8'):
    """
    Create a file at outpath and write evrey object in iterable to its
    own line.
    """
    with codecs.open(outpath, u'w+', encoding=encoding) as f:
        for s in iterable:
            f.write(s + u'\n')


@alg.unibarrier
def make_deldict(outpath, words, depth):
    """
    Creates a symmetric deletion dictionary from the specified word list.
    WARNING! This is a naive approach, which requires all the variants to be
    stored in memory. For large dictionaries at higher depth, this can easily
    use all available memory on most machines.
    """
    variant_dict = {}
    for word in words:
        for var in alg.strings_by_deletion(word, depth):
            if var not in variant_dict:
                variant_dict[var] = []
            variant_dict[var].append(word)
    ordered = sorted(variant_dict.keys())

    with codecs.open(outpath, u'w+', encoding='utf-8') as outfile:
        for key in ordered:
            originals = u' '.join(variant_dict[key])
            outfile.write(u'%s\t%s' % (key, originals) + u'\n')
