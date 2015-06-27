# -*- coding: utf-8 -*-
"""
nidaba.plugins.kraken
~~~~~~~~~~~~~~~~~~~~~

Plugin implementing access to kraken functions.

`kraken <https://mittagessen.github.io/kraken>`_ is a fork of OCRopus
implementing sane interfaces while preserving (mostly) functional equivalence.
To use this plugin kraken has to be installed into the current python path,
e.g. the current virtualenv. It is available from pypi::

    $ pip install kraken

It should be able to utilize any model trained for ocropus and is configured
using the same global configuration options.
"""

from __future__ import absolute_import

import os
import shutil

from nidaba import uzn
from nidaba import storage
from nidaba.config import nidaba_cfg
from nidaba.celery import app
from nidaba.nidabaexceptions import NidabaInvalidParameterException
from nidaba.nidabaexceptions import NidabaPluginException
from nidaba.tasks.helper import NidabaTask

from PIL import Image


def setup(*args, **kwargs):
    try:
        global binarization
        global pageseg
        global rpred
        global html
        global models
        from kraken import binarization
        from kraken import pageseg
        from kraken import rpred
        from kraken import html
        from kraken.lib import models
    except ImportError as e:
        raise NidabaPluginException(e.message)


@app.task(base=NidabaTask, name=u'nidaba.segmentation.kraken')
def segmentation_kraken(doc, method=u'segment_kraken'):
    """
    Performs page segmentation using kraken's built-in algorithm and writes an
    UNLV zone file.

    Args:

    Returns:
        Two storage tuples with the first one containing the segmentation and
        the second one being the file the segmentation was calculated upon.
    """
    input_path = storage.get_abs_path(*doc)
    output_path, ext = os.path.splitext(storage.insert_suffix(input_path,
                                        method))
    shutil.copy2(input_path, output_path + ext)
    img = Image.open(input_path)
    with open(output_path + '.uzn', 'w') as fp:
        zones = uzn.UZNWriter(fp)
        zones.writerows(pageseg.segment(img))

    return (storage.get_storage_path(output_path + '.uzn'),
            storage.get_storage_path(output_path + ext))


@app.task(base=NidabaTask, name=u'nidaba.ocr.kraken')
def ocr_kraken(doc, method=u'ocr_kraken', model=None):
    """
    Runs kraken on an input document and writes a hOCR file.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string append to all output files
        model (unicode): Identifier for the font model to use

    Returns:
        (unicode, unicode): Storage tuple for the output file
    """
    input_path = storage.get_abs_path(*doc[1])
    output_path = (doc[1][0], os.path.splitext(storage.insert_suffix(doc[1][1],
                                                                  method,
                                                                  model))[0] +
                   '.hocr')
    lines = storage.get_abs_path(*doc[0])
    if model in nidaba_cfg['kraken_models']:
        model = storage.get_abs_path(*(nidaba_cfg['kraken_models'][model]))
    elif model in nidaba_cfg['ocropus_models']:
        model = storage.get_abs_path(*(nidaba_cfg['ocropus_models'][model]))
    else:
        raise NidabaInvalidParameterException('Model not defined in '
                                              'configuration')

    storage.write_text(*output_path, text=ocr(input_path, lines, model))
    return output_path


def ocr(image_path, segmentation_path, model=None):
    """
    Runs kraken on an input document and writes a hOCR file.

    Args:
        image_path (unicode): Path to the input image
        segmentation_path (unicode): Path to the UZN file
        model (unicode): Path to the ocropus model

    Returns:
        A string containing the hOCR output.
    """
    img = Image.open(image_path)
    lines = [tuple(x[:-1]) for x in uzn.UZNReader(open(segmentation_path, 'r'))]
    rnn = models.load_any(model)
    hocr = html.hocr(list(rpred.rpred(rnn, img, lines)), image_path, img.size)
    return unicode(hocr)


@app.task(base=NidabaTask, name=u'nidaba.binarize.nlbin')
def nlbin(doc, method=u'nlbin', threshold=0.5, zoom=0.5, escale=1.0,
          border=0.1, perc=80, range=20, low=5, high=90):
    """
    Binarizes an input document utilizing ocropus'/kraken's nlbin algorithm.

    Args:
        doc (unicode, unicode): The input document tuple.
        method (unicode): The suffix string appended to all output files.
        threshold (float):
        zoom (float):
        escale (float):
        border (float)
        perc (int):
        range (int):
        low (int):
        high (int):

    Returns:
        (unicode, unicode): Storage tuple of the output file

    Raises:
        NidabaInvalidParameterException: Input parameters are outside the valid
                                         range.

    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method, unicode(threshold),
                                        unicode(zoom), unicode(escale),
                                        unicode(border), unicode(perc),
                                        unicode(range), unicode(low),
                                        unicode(high))
    kraken_nlbin(input_path, output_path, threshold, zoom, escale, border,
                 perc, range, low, high)
    return storage.get_storage_path(output_path)


def kraken_nlbin(input_path, output_path, threshold=0.5, zoom=0.5, escale=1.0,
                 border=0.1, perc=80, range=20, low=5, high=90):
    """
    Binarizes an input document utilizing ocropus'/kraken's nlbin algorithm.

    Args:
        input_path (unicode): Path to the input image
        output_path (unicode): Path to the output image
        threshold (float):
        zoom (float):
        escale (float):
        border (float)
        perc (int):
        range (int):
        low (int):
        high (int):

    Raises:
        NidabaInvalidParameterException: Input parameters are outside the valid
                                         range.

    """
    img = Image.open(input_path)
    binarization.nlbin(img, threshold, zoom, escale, border, perc, range, low,
                       high).save(output_path)
