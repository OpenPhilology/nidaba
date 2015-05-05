# -*- coding: utf-8 -*-
"""
nidaba.tasks.stats
~~~~~~~~~~~~~~~~~~

Various tasks calculating metrics on documents.

"""

from __future__ import absolute_import, unicode_literals

import os

from nidaba.tasks.helper import NidabaTask
from nidaba.algorithms import string
from nidaba.celery import app
from nidaba import storage


@app.task(base=NidabaTask, name=u'nidaba.stats.text_error_rate')
def text_error_rate(doc, method=u'error_rate', ground_truth=None, divert=True):
    """
    Estimates the error rate (edit distance) between an input document and a
    given ground truth.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to the output file.
        ground_truth (unicode): Ground truth location tuple
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
    edist = string.edit_distance(storage.retrieve_text(*doc),
                                 storage.retrieve_text(*ground_truth))
    print(edist)
    if not divert:
        return output_path
    else:
        return {'error_rate': (doc, edist), 'doc': doc}
