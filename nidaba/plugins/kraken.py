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

from __future__ import unicode_literals, print_function, absolute_import

import os
import shutil

from nidaba import uzn
from nidaba import storage
from nidaba.tei import TEIFacsimile
from nidaba.config import nidaba_cfg
from nidaba.celery import app
from nidaba.nidabaexceptions import NidabaInvalidParameterException
from nidaba.nidabaexceptions import NidabaPluginException
from nidaba.tasks.helper import NidabaTask

from PIL import Image
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def setup(*args, **kwargs):
    try:
        global binarization
        global pageseg
        global rpred
        global models
        from kraken import binarization
        from kraken import pageseg
        from kraken import rpred
        from kraken.lib import models
    except ImportError as e:
        raise NidabaPluginException(e.message)


@app.task(base=NidabaTask, name=u'nidaba.segmentation.kraken')
def segmentation_kraken(doc, method=u'segment_kraken', black_colseps=False):
    """
    Performs page segmentation using kraken's built-in algorithm and writes a
    skeleton TEI file.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string append to all output files
        black_colseps (bool): Assume black column separator instead of white
        ones.

    Returns:
        Two storage tuples with the first one containing the segmentation and
        the second one being the file the segmentation was calculated upon.
    """

    input_path = storage.get_abs_path(*doc)
    output_path, ext = os.path.splitext(storage.insert_suffix(input_path,
                                        method))
    logger.debug('Copying input image {} to {}'.format(input_path, output_path))
    shutil.copy2(input_path, output_path + ext)
    logger.debug('Reading image using PIL')
    img = Image.open(input_path)
    with open(output_path + '.xml', 'w') as fp:
        logger.debug('Initializing TEI with {} ({} {})'.format(doc[1], *img.size))
        tei = TEIFacsimile()
        tei.document(img.size, os.path.join(*doc))
        tei.title = os.path.basename(doc[1])
        tei.add_respstmt('kraken', 'page segmentation')
        for seg in pageseg.segment(img, black_colseps):
            logger.debug('Found line at {} {} {} {}'.format(*seg))
            tei.add_line(seg)
        logger.debug('Write segmentation to {}'.format(fp.name))
        tei.write(fp)
    return (storage.get_storage_path(output_path + '.xml'),
            storage.get_storage_path(output_path + ext))


@app.task(base=NidabaTask, name=u'nidaba.ocr.kraken')
def ocr_kraken(doc, method=u'ocr_kraken', model=None):
    """
    Runs kraken on an input document and writes a TEI file.

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
                                                                     model))[0]
                   + '.xml')
    logger.debug('Searching for model {}'.format(model))
    if model in nidaba_cfg['kraken_models']:
        model = storage.get_abs_path(*(nidaba_cfg['kraken_models'][model]))
    elif model in nidaba_cfg['ocropus_models']:
        model = storage.get_abs_path(*(nidaba_cfg['ocropus_models'][model]))
    else:
        raise NidabaInvalidParameterException('Model not defined in '
                                              'configuration')
    img = Image.open(input_path)
    logger.debug('Reading TEI segmentation from {}'.format(doc[1]))
    tei = TEIFacsimile()
    with storage.StorageFile(*doc[0]) as seg:
        tei.read(seg)

    logger.debug('Clearing out word/grapheme boxes')
    # kraken is a line recognizer
    tei.clear_graphemes()
    tei.clear_segments()
    # add and scope new responsibility statement
    tei.add_respstmt('kraken', 'character recognition')
    lines = tei.lines

    logger.debug('Loading model {}'.format(model))
    rnn = models.load_any(model)
    i = 0
    logger.debug('Start recognizing characters')
    for rec in rpred.rpred(rnn, img, [(int(x[0]), int(x[1]), int(x[2]), int(x[3])) for x in lines]):
        # scope the current line and add all graphemes recognized by kraken to
        # it.
        logger.debug('Scoping line {}'.format(line[i][4]))
        tei.scope_line(lines[i][4])
        logger.debug('Adding graphemes: {}'.format(rec.prediction))
        tei.add_graphemes([(x[0], x[1], int(x[2] * 100)) for x in rec])
        i += 1
    with storage.StorageFile(*output_path, mode='wb') as fp:
        logger.debug('Writing TEI to {}'.format(fp.name))
        tei.write(fp)
    return output_path


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
