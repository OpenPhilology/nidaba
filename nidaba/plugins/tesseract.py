# -*- coding: utf-8 -*-
"""
nidaba.plugins.tesseract
~~~~~~~~~~~~~~~~~~~~~~~~

Plugin implementing an interface to tesseract
"""

from __future__ import absolute_import

import subprocess
import ctypes

from PIL import Image

from nidaba import storage
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaTesseractException


implementation = u'capi'
tessdata = u'/usr/share/tesseract-ocr/'


def setup(*args, **kwargs):
    if kwargs.get(u'implementation'):
        implementation = kwargs.get(u'implementation')
    if kwargs.get(u'tessdata'):
        tessdata = kwargs.get(u'tessdata')


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
    image_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(image_path, method, *languages)

    if implementation == 'legacy':
        result_path = output_path + '.html'
        ocr_direct(image_path, output_path, languages)
    elif implementation == 'direct':
        result_path = output_path + '.hocr'
        ocr_direct(image_path, output_path, languages)
    elif implementation == 'capi':
        result_path = output_path + '.hocr'
        ocr_capi(image_path, result_path, languages)
    else:
        raise NidabaTesseractException('Invalid implementation selected',
                                       implementation)
    return storage.get_storage_path(result_path)


def ocr_capi(image_path, output_path, languages):
    """
    OCRs an image using the C API provided by tesseract versions 3.02 and
    higher. Images are read using pillow allowing a wider range of formats than
    leptonica and results are written to a fixed output document.

    Args:
        image_path (unicode): Path to the input image
        output_path (unicode): Path to the hOCR output
        languages (list): List of valid tesseract language identifiers
    """

    img = Image.open(image_path)
    w, h = img.size

    assert img.mode == 'L' or img.mode == '1'
    tesseract = ctypes.cdll.LoadLibrary('libtesseract.so.3')
    api = tesseract.TessBaseAPICreate()
    rc = tesseract.TessBaseAPIInit3(api, str(tessdata), str('+'.join(languages)))
    if (rc):
        tesseract.TessBaseAPIDelete(api)

    tesseract.TessBaseAPISetImage(api, ctypes.c_char_p(img.tobytes()), w, h, 1, w)
    with open(output_path, 'wb') as fp:
        hocr = ctypes.string_at(tesseract.TessBaseAPIGetHOCRText(api))
        fp.write(hocr)


def ocr_direct(image_path, output_path, languages):
    """
    OCRs an image by calling the tesseract executable directly. Images are read
    using the linked leptonica library and the given output_path WILL be
    modified by tesseract.

    Args:
        image_path (unicode): Path to the input image
        output_path (unicode): Path to the hOCR output
        languages (list): List of valid tesseract language identifiers
    """

    p = subprocess.Popen(['tesseract', image_path, output_path, '-l',
                          '+'.join(languages), '--tessdata-dir', tessdata,
                          'hocr'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise NidabaTesseractException(err)
