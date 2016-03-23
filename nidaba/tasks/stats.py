# -*- coding: utf-8 -*-
"""
nidaba.tasks.stats
~~~~~~~~~~~~~~~~~~

Various tasks calculating metrics on documents.

"""

from __future__ import unicode_literals, print_function, absolute_import

import os
import difflib
import StringIO

from lxml import html
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance, damerau_levenshtein_distance

from nidaba import storage
from nidaba.tei import OCRRecord
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.algorithms.string import sanitize
from nidaba.nidabaexceptions import NidabaInvalidParameterException

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

def cleanup(text):
    """
    Removes lines containing only whitespace and normalizes to NFD.
    """
    text = sanitize(text)
    return '\n'.join([s for s in text.splitlines() if len(s.strip())])

def find_matching(doc, ground_truths):
    """
    Extracts a probable ground truth from a list of files based on prefix
    match.
    """
    def cmp_prefix(x, y):
        return len(os.path.commonprefix([y[1], doc[1]])) - len(os.path.commonprefix([x[1], doc[1]]))
    return sorted(ground_truths, cmp=cmp_prefix)[0]

@app.task(base=NidabaTask, name=u'nidaba.stats.text_diff_ratio',
          arg_values={'ground_truth': 'files',
                      'xml_in': [True, False],
                      'gt_format': ['tei', 'hocr', 'text'],
                      'clean_in': [True, False],
                      'clean_gt': [True, False],
                      'divert': [True, False]})
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
        ground_truth (unicode): Ground truth location tuple or a list of ground
                                truths to choose from. When more than one is
                                given, the file sharing the longest prefix with
                                the input document is chosen.
        xml_in (bool): Switch to treat input as an TEI-XML document.
        gt_format (unicode): Switch to select ground truth format. Valid values
                             are 'tei', 'hocr', and 'text'.
        clean_in (bool): Normalize to NFD and strip input data. (DO NOT DISABLE!)
        clean_gt (bool): Normalize to NFD and strip ground truth. (DO NOT DISABLE!)
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
    if not isinstance(ground_truth[0], basestring):
        ground_truth = find_matching(doc, ground_truth)
    with storage.StorageFile(*ground_truth) as fp:
        if gt_format == 'tei':
            tei = OCRRecord()
            tei.load_tei(fp)
            t = StringIO.StringIO()
            tei.write_text(t)
            gt = t.getvalue()
        elif gt_format == 'hocr':
            gt = html.parse(fp).text_content()
        elif gt_format == 'text':
            gt = fp.read()
        else:
            raise NidabaInvalidParameterException('Input format ' + gt_format + ' unknown.')
    with storage.StorageFile(*doc) as fp:
        if xml_in:
            tei = OCRRecord()
            tei.load_tei(fp)
            t = StringIO.StringIO()
            tei.write_text(t)
            text = t.getvalue()
        else:
            text = fp.read()
    if clean_in:
        text = cleanup(text)
    if clean_gt:
        gt = cleanup(gt)
    logger.debug('Recognition result: \n{}'.format(text))
    logger.debug('Ground truth: \n{}'.format(gt))
    sm = difflib.SequenceMatcher()
    sm.set_seqs(text, gt)
    logger.debug('Accuracy: {}'.format(sm.ratio()))
    if not divert:
        storage.write_text(*storage.get_storage_path(output_path),
                           text=unicode(sm.ratio()))
        return output_path
    else:
        return {'diff_ratio': sm.ratio(), 'ground_truth': ground_truth, 'doc': doc}


@app.task(base=NidabaTask, name=u'nidaba.stats.text_edit_ratio',
          arg_values={'ground_truth': 'files',
                      'xml_in': [True, False],
                      'gt_format': ['tei', 'hocr', 'text'],
                      'clean_in': [True, False],
                      'clean_gt': [True, False],
                      'divert': [True, False]})
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
        ground_truth (unicode): Ground truth location tuple or a list of ground
                                truths to choose from. When more than one is
                                given, the file sharing the longest prefix with
                                the input document is chosen.
        xml_in (bool): Switch to treat input as an TEI-XML document.
        gt_format (unicode): Switch to select ground truth format. Valid values
                             are 'tei', 'hocr', and 'text'.
        clean_in (bool): Normalize to NFD and strip input data. (DO NOT DISABLE!)
        clean_gt (bool): Normalize to NFD and strip ground truth. (DO NOT DISABLE!)
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
    if not isinstance(ground_truth[0], basestring):
        ground_truth = find_matching(doc, ground_truth)
    with storage.StorageFile(*ground_truth) as fp:
        if gt_format == 'tei':
            tei = OCRRecord()
            tei.load_tei(fp)
            t = StringIO.StringIO()
            tei.write_text(t)
            gt = t.getvalue()
        elif gt_format == 'hocr':
            gt = html.parse(fp).text_content()
        elif gt_format == 'text':
            gt = fp.read()
        else:
            raise NidabaInvalidParameterException('Input format ' + gt_format + ' unknown.')
    with storage.StorageFile(*doc) as fp:
        if xml_in:
            tei = OCRRecord()
            tei.load_tei(fp)
            t = StringIO.StringIO()
            tei.write_text(t)
            text = t.getvalue()
        else:
            text = fp.read()
    if clean_in:
        text = cleanup(text)
    if clean_gt:
        gt = cleanup(gt)
    logger.debug('Recognition result: \n{}'.format(text))
    logger.debug('Ground truth: \n{}'.format(gt))
    edist = 1.0 - normalized_damerau_levenshtein_distance(text, gt)
    logger.debug('Edit distance: {}'.format(damerau_levenshtein_distance(text, gt)))
    logger.debug('Accuracy: {}'.format(edist))
    if not divert:
        storage.write_text(*storage.get_storage_path(output_path),
                           text=unicode(edit))
        return output_path
    else:
        return {'edit_ratio': edist, 'ground_truth': ground_truth, 'doc': doc}
