# -*- coding: utf-8 -*-
"""
iris.tasks.ocr
~~~~~~~~~~~~~~

Tasks running optical character recognition on a binarized image. As of now
this encapsulates page segmentation, recognition, and in the case of Tesseract
language model application in a single task.

"""

from __future__ import absolute_import, unicode_literals

from iris import tesseract
from iris import ocropus
from iris import storage
from iris.config import iris_cfg
from iris.celery import app
from iris.tasks.helper import IrisTask

import os

@app.task(base=IrisTask, name=u'iris.ocr.tesseract')
def ocr_tesseract(doc, id, method=u'ocr_tesseract', languages=None):
    """
    Runs tesseract on an input document.
    
    Args:
        doc (unicode, unicode): The input document tuple
        id (unicode): The iris batch identifier this task is a part of
        method (unicode): The suffix string appended to all output files
        languages (list of unicode): A list of languages for the tesseract language model
        
    Returns:
        (unicode, unicode): Storage tuple for the output file
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method, *languages)
    return storage.get_storage_path(tesseract.ocr(input_path, output_path, languages))

@app.task(base=IrisTask, name=u'iris.ocr.ocropus')
def ocr_ocropus(doc, id, method=u'ocr_ocropus', model=None):
    """
    Runs ocropus on an input document.

    Args:
        doc (unicode, unicode): The input document tuple
        id (unicode): The iris batch identifier this task is a part of
        method (unicode): The suffix string appended to all output files
        model (unicode): Identifier for the font model to use
        
    Returns:
        (unicode, unicode): Storage tuple for the output file
   
    """
    input_path = storage.get_abs_path(*doc)
    output_path = os.path.splitext(storage.insert_suffix(input_path, method, model))[0] + '.html'
    model = storage.get_abs_path(*(iris_cfg['ocropus_models'][model]))
    return storage.get_storage_path(ocropus.ocr(input_path, output_path, model))

