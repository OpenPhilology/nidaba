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

from nidaba import storage
from nidaba.tei import TEIFacsimile
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.algorithms.string import sanitize
from nidaba.nidabaexceptions import NidabaInvalidParameterException


def cleanup(text):
    """
    Removes lines containing only whitespace and normalizes to NFD.
    """
    text = sanitize(text)
    return '\n'.join([s for s in text.splitlines() if len(s.strip())])


@app.task(base=NidabaTask, name=u'nidaba.stats.text_diff_ratio')
def text_diff_ratio(doc, method=u'text_diff_ratio', ground_truth=None,
                    xml_in=True, gt_format=u'tei', clean_in=True, clean_gt=True,
                    divert=True):
    """
    Calculates the similarity of the input documents and a given ground truth
    using the algorithm of python's difflib SequenceMatcher. The result is a
    value between 0.0 (no commonality) and 1.0 (identical strings).

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to the output file.
        ground_truth (unicode): Ground truth location tuple
        xml_in (bool): Switch to treat input as an TEI-XML document.
        gt_format (unicode): Switch to select ground truth format. Valid values
                             are 'tei', 'hocr', and 'text'.
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
    with storage.StorageFile(*ground_truth) as fp:
        if gt_format == 'tei':
            tei = TEIFacsimile()
            tei.read(fp)
            gt = '\n'.join(x[-1] for x in tei.lines)
        elif gt_format == 'hocr':
            gt = html.parse(fp).text_content()
        elif gt_format == 'text':
            gt = fp.read()
        else:
            raise NidabaInvalidParameterException('Input format ' + gt_format + ' unknown.')
    with storage.StorageFile(*doc) as fp:
        if xml_in:
            tei = TEIFacsimile()
            tei.read(fp)
            text = '\n'.join(x[-1] for x in tei.lines)
        else:
           text = fp.read()
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
                    xml_in=True, gt_format='tei', clean_in=True, clean_gt=True,
                    divert=True):
    """
    Calculates the similarity of the input documents and a given ground truth
    using the Damerau-Levenshtein distance. The result is a value between 0.0
    (no commonality) and 1.0 (identical strings).

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to the output file.
        ground_truth (unicode): Ground truth location tuple
        xml_in (bool): Switch to treat input as an TEI-XML document.
        gt_format (unicode): Switch to select ground truth format. Valid values
                             are 'tei', 'hocr', and 'text'.
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
    with storage.StorageFile(*ground_truth) as fp:
        if gt_format == 'tei':
            tei = TEIFacsimile()
            tei.read(fp)
            gt = '\n'.join(x[-1] for x in tei.lines)
        elif gt_format == 'hocr':
            gt = html.parse(fp).text_content()
        elif gt_format == 'text':
            gt = fp.read()
        else:
            raise NidabaInvalidParameterException('Input format ' + gt_format + ' unknown.')
    with storage.StorageFile(*doc) as fp:
        if xml_in:
            tei = TEIFacsimile()
            tei.read(fp)
            text = '\n'.join(x[-1] for x in tei.lines)
        else:
           text = fp.read()
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
