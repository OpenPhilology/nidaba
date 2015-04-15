# -*- coding: utf-8 -*-
"""
nidaba.tasks.util
~~~~~~~~~~~~~~~~~

Various utility tasks that either can't be classified by purpose or are one of
a kind.

"""

from __future__ import absolute_import, unicode_literals

from nidaba.tasks.helper import NidabaTask
from nidaba.celery import app
from nidaba import storage
from nidaba import merge_hocr


@app.task(base=NidabaTask, name=u'nidaba.util.blend_hocr')
def blend_hocr(doc, method=u'blend_hocr', language=u''):
    """
    Blends multiple hOCR files using the algorithm from Bruce Robertsons
    rigaudon. It requires a working spell checking for the input document's
    language; otherwise all matched bboxes will be bunched together without any
    scoring.

    Args:
        doc [(id, path), ...]: A list of storage module tupels that will be
        merged into a single output document.
        id (unicode): The nidaba batch identifier this task is a part of
                      language (unicode): Language used for spell-checking
                      based scoring. If not defined no scoring will be used.
        method (unicode): The suffix string appended to the output file.

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    # create the output document path from the first input document
    input_path = storage.get_abs_path(*doc[0])
    output_path = storage.insert_suffix(input_path, method)
    return merge_hocr.merge(doc, language,
                            storage.get_storage_path(output_path))


@app.task(base=NidabaTask, name=u'nidaba.util.sync')
def sync(doc):
    """
    Takes ones argument and returns it. Used to synchronized stuff as
    chaining groups is not possible with the current celery version.

    Args:
        doc: An arbitrary input argument

    Returns:
        The input argument unaltered
    """
    return doc
