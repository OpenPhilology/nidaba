# -*- coding: utf-8 -*-
"""
nidaba.tasks.stats
~~~~~~~~~~~~~~~~~~

Various tasks calculating metrics on documents.

"""

from __future__ import absolute_import, unicode_literals

import os
import difflib

from lxml import html
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance

from nidaba.algorithms.string import sanitize
from nidaba.tasks.helper import NidabaTask
from nidaba.celery import app
from nidaba import storage


def cleanup(text):
    """
    Removes lines containing only whitespace and normalizes to NFD.
    """
    text = sanitize(text)
    return '\n'.join([s for s in text.splitlines() if len(s.strip())])


@app.task(base=NidabaTask, name=u'nidaba.stats.text_diff_ratio')
def text_diff_ratio(doc, method=u'text_diff_ratio', ground_truth=None,
                    hocr_in=True, hocr_gt=False, clean_in=True, clean_gt=True,
                    divert=True):
    """
    Calculates the similarity of the input documents and a given ground truth
    using the algorithm of python's difflib SequenceMatcher. The result is a
    value between 0.0 (no commonality) and 1.0 (identical strings).

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to the output file.
        ground_truth (unicode): Ground truth location tuple
        hocr_in (bool): Switch to treat input as a hOCR document.
        hocr_gt (bool): Switch to treat ground truth as a hOCR document.
        divert (bool): Switch selecting output diversion. If enabled the output
                       will be added to the tracking arguments and the input
                       document will be returned as the result of the task. Use
                       this to insert a statistical measure into a chain
                       without affecting the results.

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    input_path = storage.get_abs_path(*doc[0])
    output_path = storage.insert_suffix(input_path, method,
                                        os.path.basename(input_path))
    text = storage.retrieve_text(*doc)[doc[1]]
    gt = storage.retrieve_text(*ground_truth)[ground_truth[1]]
    if hocr_in:
        text = html.fromstring(text.encode('utf-8')).text_content()
    if hocr_gt:
        gt = html.fromstring(gt.encode('utf-8')).text_content()
    if clean_in:
        text = cleanup(text)
    if clean_gt:
        gt = cleanup(gt)
    sm = difflib.SequenceMatcher()
    sm.set_seqs(text, gt)
    if not divert:
        storage.write_text(*get_storage_path(output_path), text=unicode(sm.ratio()))
        return output_path
    else:
        return {'diff_ratio': sm.ratio(), 'doc': doc}


@app.task(base=NidabaTask, name=u'nidaba.stats.text_edit_ratio')
def text_edit_ratio(doc, method=u'text_edit_ratio', ground_truth=None,
                    hocr_in=True, hocr_gt=False, clean_in=True, clean_gt=True,
                    divert=True):
    """
    Calculates the similarity of the input documents and a given ground truth
    using the Damerau-Levenshtein distance. The result is a value between 0.0
    (no commonality) and 1.0 (identical strings).

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to the output file.
        ground_truth (unicode): Ground truth location tuple
        hocr_in (bool): Switch to treat input as a hOCR document.
        hocr_gt (bool): Switch to treat ground truth as a hOCR document.
        divert (bool): Switch selecting output diversion. If enabled the output
                       will be added to the tracking arguments and the input
                       document will be returned as the result of the task. Use
                       this to insert a statistical measure into a chain
                       without affecting the results.

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    input_path = storage.get_abs_path(*doc[0])
    output_path = storage.insert_suffix(input_path, method,
                                        os.path.basename(input_path))
    text = storage.retrieve_text(*doc)[doc[1]]
    gt = storage.retrieve_text(*ground_truth)[ground_truth[1]]
    if hocr_in:
        text = html.fromstring(text.encode('utf-8')).text_content()
    if hocr_gt:
        gt = html.fromstring(gt.encode('utf-8')).text_content()
    if clean_in:
        text = cleanup(text)
    if clean_gt:
        gt = cleanup(gt)
    edist = 1.0 - normalized_damerau_levenshtein_distance(text, gt)
    if not divert:
        storage.write_text(*get_storage_path(output_path), text=unicode(edit))
        return output_path
    else:
        return {'edit_ratio': edist, 'doc': doc}
