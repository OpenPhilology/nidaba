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
import regex

from nidaba import storage
from nidaba.tei import OCRRecord
from nidaba.config import nidaba_cfg
from nidaba.celery import app
from nidaba.nidabaexceptions import NidabaInvalidParameterException
from nidaba.nidabaexceptions import NidabaPluginException
from nidaba.tasks.helper import NidabaTask

from PIL import Image
from itertools import izip_longest
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


def max_bbox(boxes):
    """ 
    Calculates the minimal bounding box containing all boxes contained in an
    iterator.

    Args:
        boxes (iterator): An iterator returning tuples of the format (x0, y0,
                          x1, y1)
    Returns:
        A box covering all bounding boxes in the input argument
    """
    sbox = list(map(sorted, list(zip(*boxes))))
    return (sbox[0][0], sbox[1][0], sbox[2][-1], sbox[3][-1])


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
        tei = OCRRecord()
        tei.img = storage.get_url(*doc)
        tei.dimensions = img.size
        tei.title = os.path.basename(doc[1])
        tei.add_respstmt('kraken', 'page segmentation')
        for seg in pageseg.segment(img, black_colseps):
            logger.debug('Found line at {} {} {} {}'.format(*seg))
            tei.add_line(seg)
        logger.debug('Write segmentation to {}'.format(fp.name))
        tei.write_tei(fp)
    return (storage.get_storage_path(output_path + '.xml'),
            storage.get_storage_path(output_path + ext))


@app.task(base=NidabaTask, name=u'nidaba.ocr.kraken',
          arg_values={'model': nidaba_cfg['ocropus_models'].keys() +
                               nidaba_cfg['kraken_models'].keys()})
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
    tei = OCRRecord()
    with storage.StorageFile(*doc[0]) as seg:
        tei.load_tei(seg)

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
    for line_id, rec in zip(lines, rpred.rpred(rnn, img, [x['bbox'] for x in lines.itervalues()])):
        # scope the current line and add all graphemes recognized by kraken to
        # it.
        logger.debug('Scoping line {}'.format(line_id))
        tei.scope_line(line_id)
        i += 1

        splits = regex.split(u'(\s+)', rec.prediction)
        line_offset = 0
        for segment, whitespace in izip_longest(splits[0::2], splits[1::2]):
            if len(segment):
                seg_bbox = max_bbox(rec.cuts[line_offset:line_offset + len(segment)])
                logger.debug('Creating new segment at {} {} {} {}'.format(*seg_bbox))
                tei.add_segment(seg_bbox)
                logger.debug('Adding graphemes (segment): {}'.format(rec.prediction[line_offset:line_offset+len(segment)]))
                tei.add_graphemes([{'grapheme': x[0], 
                                    'bbox': x[1],
                                    'confidence': int(x[2] * 100)} for x in rec[line_offset:line_offset+len(segment)]])
                line_offset += len(segment)
            if whitespace:
                logger.debug('Adding graphemes (whitespace): {}'.format(rec.prediction[line_offset:line_offset+len(whitespace)]))
                seg_bbox = max_bbox(rec.cuts[line_offset:line_offset + len(whitespace)])
                tei.add_segment(seg_bbox)
                tei.add_graphemes([{'grapheme': x[0], 
                                    'bbox': x[1],
                                    'confidence': int(x[2] * 100)} for x in rec[line_offset:line_offset+len(whitespace)]])
                line_offset += len(whitespace)
    with storage.StorageFile(*output_path, mode='wb') as fp:
        logger.debug('Writing TEI to {}'.format(fp.abs_path))
        tei.write_tei(fp)
    return output_path


@app.task(base=NidabaTask, name=u'nidaba.binarize.nlbin',
          arg_values={'threshold': (0.0, 1.0),
                                      'zoom': (0.0, 1.0),
                                      'escale': 'float',
                                      'border': 'float',
                                      'perc': (0, 100),
                                      'range': (0, 100),
                                      'low': (0, 100),
                                      'high': (0, 100)})
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
    img = Image.open(input_path)
    o_img = binarization.nlbin(img, threshold, zoom, escale, border, perc, range, low,
                       high)
    o_img.save(output_path)
    return storage.get_storage_path(output_path)
