# -*- coding: utf-8 -*-
"""
nidaba.plugins.tesseract
~~~~~~~~~~~~~~~~~~~~~~~~

Plugin implementing an interface to tesseract
"""

from __future__ import absolute_import

import subprocess

from nidaba import storage
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaTesseractException
from nidaba.config import nidaba_cfg


def setup(*args, **kwargs):
    pass


@app.task(base=NidabaTask, name=u'nidaba.ocr.tesseract')
def ocr_tesseract(doc, method=u'ocr_tesseract', languages=None):
    """
    Runs tesseract on an input document.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files
                          languages (list of unicode): A list of languages for
                          the tesseract language model

    Returns:
        (unicode, unicode): Storage tuple for the output file
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method, *languages)
    return storage.get_storage_path(ocr(input_path, output_path, languages))


def ocr(imagepath, outputfilepath, languages):
    """
    Scan a single image with tesseract using the specified language,
    and writing output to the specified file.

    Args:
        imagepath (unicode): Path to the image file
        outputfilepath (unicode): Path to the output file. Tesseract will
                                  independently append either .html or .hocr to
                                  this path.
        languages (list): A list of strings containing valid tesseract language
                          descriptions.
    Returns:
        unicode: Path of the output file.

    Raise:
        NidabaTesseractException: Tesseract quit with a return code other than
                                  0.
    """
    p = subprocess.Popen(['tesseract', '-l', '+'.join(languages), imagepath,
                         outputfilepath, 'hocr'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if nidaba_cfg['legacy_tesseract']:
        resultpath = outputfilepath + '.html'
    else:
        resultpath = outputfilepath + '.hocr'
    out, err = p.communicate()
    if p.returncode:
        raise NidabaTesseractException(err)
    return resultpath
