# -*- coding: utf-8 -*-
"""
nidaba.lex
~~~~~~~~~~

This module contains functions for dealing with words and dictionaries, such as
extracting words from texts, normalizing encodings, building symmetric deletion
dictionaries, etc.
"""

from __future__ import absolute_import

import os
import codecs
import glob
import nidaba.algorithms.string as alg
from collections import Counter


@alg.unibarrier
def cleanlines(path, encoding=u'utf-8', normalization=u'NFD'):
    """
    Read in lines from a file and return them as a sanitized list.
    Non-unique linse will be repeated.

    Args:
        path (unicode): Absolute path of the file to be read
        encoding (unicode): Encoding to use for decoding the file
        normalization (unicode): Normalization format to use

    Returns:
        list: List of lines containing the sanitized output, i.e. normalized
              unicode objects.
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
    Non-unique words will be repeated as they are read in. Detects only words
    divided by a standard space.

    Args:
        path (unicode): Absolute path of the file to be read
        encoding (unicode): Encoding to use for decoding the file
        normalization (unicode): Normalization format to use

    Returns:
        list: List of words containing the sanitized output, i.e. normalized
              unicode objects.
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

    Args:
        path (unicode): Absolute path of the file to be read
        encoding (unicode): Encoding to use for decoding the file
        normalization (unicode): Normalization format to use

    Returns:
        Counter: Contains the frequency of each token
    """
    words = cleanwords(path, encoding=encoding, normalization=normalization)
    freq = Counter(words)
    return freq


@alg.unibarrier
def cleanuniquewords(path, encoding=u'utf-8', normalization=u'NFD'):
    """
    Read in lines from a file as separated by lines and spaces,
    convert them to the specified normalization, and return a set
    of all unique words.

    Args:
        path (unicode): Absolute path of the file to be read
        encoding (unicode): Encoding to use for decoding the file
        normalization (unicode): Normalization format to use

    Returns:
        set: Set of unique tokens
    """
    return set(cleanwords(path, encoding=encoding,
                          normalization=normalization))


@alg.unibarrier
def words_from_files(dirpath, encoding=u'utf-8', normalization=u'NFD'):
    """
    Create a dictionary from a directory of text files.  All files in the given
    directory will be parsed.

    Args:
        dirpath (unicode): Absolute path of the directory to enter
        encoding (unicode): Encoding to use for decoding the files
        normalization (unicode): Normalization format to use

    Returns:
        list: List of words of all files in the directory
    """
    words = []
    for filename in filter(os.path.isfile, glob.glob(dirpath + '/*')):
        words += cleanwords(filename, encoding=encoding,
                            normalization=normalization)
    return words


@alg.unibarrier
def unique_words_from_files(dirpath, encoding=u'utf-8', normalization=u'NFD'):
    """
    Create a set of unique words from a directory of text files.  All file in
    the given directory will be parsed.

    Args:
        dirpath (unicode): Absolute path of the directory to enter
        encoding (unicode): Encoding to use for decoding the files
        normalization (unicode): Normalization format to use

    Returns:
        set: Set of words of all files in the directory
    """
    return set(words_from_files(dirpath, encoding=encoding,
                                normalization=normalization))


@alg.unibarrier
def make_dict(outpath, iterable, encoding=u'utf-8'):
    """
    Create a file at outpath and write evrey object in iterable to its
    own line. The file is opened in append mode.

    Args:
        outpath (unicode): File path to write to
        iterable (iterable): An iterable used as a data source
        normalization (unicode): Normalization format to use
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

    Args:
        outpath (unicode): File path to write to
        words (iterable): An iterable returning a single word per iteration
        depth (int): Maximum edit distance to calculate
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
