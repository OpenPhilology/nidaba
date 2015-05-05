# -*- coding: utf-8 -*-
"""
nidaba.plugins.tesseract
~~~~~~~~~~~~~~~~~~~~~~~~

Plugin implementing an interface to tesseract

This plugin exposes tesseract's functionality as a task. It implements two ways
of calling tesseract, a direct method calling the tesseract executable and one
utilizing the C-API available from tesseract 3.02 and upwards.

The C-API requires a libtesseract shared object in the current library path and
training data in the configured tessdata directory:

.. code-block:: console

    # apt-get install libtesseract3 tesseract-ocr-$lang

Using the direct call method requires the tesseract binary installable by
executing:

.. code-block:: console

    # apt-get install tesseract-ocr

.. note::
    It is strongly encouraged to use the C-API whenever possible. It is
    supposedly stable while hOCR output file names change between tesseract
    versions.
    
Configuration
~~~~~~~~~~~~~

implementation (default='capi')
    Selector for the call method. May either be `capi`, `direct` (tesseract
    hOCR output with .hocr extension), or `legacy` (tesseract hOCR output with
    .html extension).

tessdata (default='/usr/share/tesseract-ocr/')
    Path to load tesseract training data and configuration from. Has to be one
    directory level upwards from the actual tessdata directory
"""

from __future__ import absolute_import

import subprocess
import ctypes

from PIL import Image
from distutils import spawn

from nidaba import storage
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaTesseractException
from nidaba.nidabaexceptions import NidabaPluginException


implementation = u'capi'
tessdata = u'/usr/share/tesseract-ocr/'


def setup(*args, **kwargs):
    if kwargs.get(u'implementation'):
        global implementation
        implementation = kwargs.get(u'implementation')
    if kwargs.get(u'tessdata'):
        global tessdata
        if isinstance(kwargs.get(u'tessdata'), list):
            tessdata = storage.get_abs_path(*kwargs.get(u'tessdata'))
        else:
            tessdata = kwargs.get(u'tessdata')
    if implementation == 'direct' and not spawn.find_executable('tesseract'):
        raise NidabaPluginException('No tesseract executable found')
    if implementation == 'capi' :
        try:
            ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise NidabaPluginException('Loading libtesseract failed.')


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
    if isinstance(languages, basestring):
        languages = [languages]
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
    # There is a regression in TessBaseAPISetImage somewhere between 3.02 and
    # 3.03. Unfortunately the tesseract maintainers close all bug reports
    # concerning their API, so we just convert to grayscale here.
    img = img.convert('L')
    try:
        tesseract = ctypes.cdll.LoadLibrary('libtesseract.so.3')
    except OSError as e:
        raise NidabaTesseractException('Loading libtesseract failed: ' +
                                       e.message)

    # ensure we've loaded a tesseract object newer than 3.02
    tesseract.TessVersion.restype = ctypes.c_char_p
    ver = tesseract.TessVersion()
    if int(ver.split('.')[0]) < 3 or int(ver.split('.')[1]) < 2:
        tesseract.TessBaseAPIDelete(api)
        raise NidabaTesseractException('libtesseract version is too old. Set'
                                       'implementation to direct.')
    api = tesseract.TessBaseAPICreate()
    rc = tesseract.TessBaseAPIInit3(api, str(tessdata), str('+'.join(languages)))
    if (rc):
        tesseract.TessBaseAPIDelete(api)
        raise NidabaTesseractException('Tesseract initialization failed.')
    tesseract.TessBaseAPISetImage(api, ctypes.c_char_p(str(img.tobytes())), w, h, 1, w)
    with open(output_path, 'wb') as fp:
        tp = tesseract.TessBaseAPIGetHOCRText(api)
        fp.write(ctypes.string_at(tp))
        tesseract.TessDeleteText(tp)
    tesseract.TessBaseAPIDelete(api)

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
