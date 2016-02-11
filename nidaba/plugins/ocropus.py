# -*- coding: utf-8 -*-
"""
nidaba.plugins.ocropus
~~~~~~~~~~~~~~~~~~~~~~

Plugin implementing an interface to the `ocropus
<http://github.com/tmbdev/ocropy>`_ OCR engine.

It requires working ocropus-* tools in your execution path. Please have a look
at the website for installation instructions.

.. important::
    If you are not requiring specific functionality of ocropus please consider
    using the :mod:`kraken <nidaba.plugins.kraken>` plugin. Kraken does not
    require working around oddities in input argument acceptance and is
    generally more well-behaved than ocropus.
"""

from __future__ import unicode_literals, print_function, absolute_import

import os
import numpy as np

from PIL import Image
from celery.utils.log import get_task_logger

from nidaba import storage
from nidaba.tei import OCRRecord 
from nidaba.config import nidaba_cfg
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaOcropusException
from nidaba.nidabaexceptions import NidabaPluginException

logger = get_task_logger(__name__)


def setup(*args, **kwargs):
    try:
        global ocrolib
        import ocrolib
    except:
        raise NidabaPluginException('Prerequisites for ocropus module not '
                                    'installed.')


class micro_hocr(object):
    """
    A simple class encapsulating hOCR attributes
    """
    def __init__(self):
        self.output = u''

    def __str__(self):
        return self.output

    def add(self, *args):
        if self.output:
            self.output += u'; '
        for arg in args:
            if isinstance(arg, basestring):
                self.output += arg + ' '
            elif isinstance(arg, tuple):
                self.output += u','.join([unicode(v) for v in arg]) + u' '
            else:
                self.output += unicode(arg) + u' '
        self.output = self.output.strip()


@app.task(base=NidabaTask, name=u'nidaba.ocr.ocropus',
          arg_values={'model': nidaba_cfg['ocropus_models'].keys()})
def ocr_ocropus(doc, method=u'ocr_ocropus', model=None):
    """
    Runs ocropus on an input document.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files
        model (unicode): Identifier for the font model to use

    Returns:
        (unicode, unicode): Storage tuple for the output file

    """
    image_path = storage.get_abs_path(*doc[1])
    segmentation_path = storage.get_abs_path(*doc[0])
    output_path = os.path.splitext(storage.insert_suffix(image_path, method,
                                   model))[0] + '.xml'
    model = storage.get_abs_path(*(nidaba_cfg['ocropus_models'][model]))
    return storage.get_storage_path(ocr(image_path, segmentation_path,
                                        output_path, model))


def ocr(image_path, segmentation_path, output_path, model_path):
    """
    Scan a single image with ocropus.

    Reads a single image file from ```imagepath``` and writes the recognized
    text as a TEI document into output_path.

    Args:
        image_path (unicode): Path of the input file
        segmentation_path (unicode): Path of the segmentation XML file.
        output_path (unicode): Path of the output file
        model_path (unicode): Path of the recognition model. Must be a pyrnn.gz
                             pickle dump interoperable with ocropus-rpred.

    Returns:
        (unicode): A string of the output file that is actually written. As
                   Ocropus rewrites output file paths without notice it may be
                   different from the ```outputfilepath``` argument.

    Raises:
        NidabaOcropusException: Ocropus somehow failed. The error output is
                                contained in the message but as it is de facto
                                unusable as a library it's impossible to deduct
                                the nature of the problem.
    """

    try:
        logger.debug('Loading pyrnn from {}'.format(model_path))
        network = ocrolib.load_object(model_path, verbose=0)
        lnorm = getattr(network, "lnorm")
    except Exception as e:
        raise NidabaOcropusException('Something somewhere broke: ' + e.msg)
    im = Image.open(image_path)

    logger.debug('Loading TEI segmentation {}'.format(segmentation_path))
    tei = OCRRecord()
    with open(segmentation_path, 'r') as seg_fp:
        tei.load_tei(seg_fp)

    logger.debug('Clearing out word/grapheme boxes')
    # ocropus is a line recognizer
    tei.clear_graphemes()
    tei.clear_segments()
    # add and scope new responsibility statement
    tei.add_respstmt('ocropus', 'character recognition')
    for line_id, box in tei.lines.iteritems():
        logger.debug('Recognizing line {}'.format(box['bbox']))
        line = ocrolib.pil2array(im.crop(box['bbox']))
        temp = np.amax(line) - line
        temp = temp * 1.0 / np.amax(temp)
        lnorm.measure(temp)
        line = lnorm.normalize(line, cval=np.amax(line))
        if line.ndim == 3:
            np.mean(line, 2)
        line = ocrolib.lstm.prepare_line(line, 16)
        pred = network.predictString(line)
        pred = ocrolib.normalize_text(pred)
        logger.debug('Scoping line {}'.format(line_id))
        tei.scope_line(line_id)
        logger.debug('Adding graphemes: {}'.format(pred))
        tei.add_graphemes({'grapheme': x} for x in pred)
    with open(output_path, 'wb') as fp:
        logger.debug('Writing TEI to {}'.format(fp.name))
        tei.write_tei(fp)
    return output_path
