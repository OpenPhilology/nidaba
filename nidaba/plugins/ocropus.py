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

from __future__ import absolute_import

import subprocess
import glob
import os
import re
import shutil
import uuid
import dominate
import numpy as np

from dominate.tags import div, span, meta, br
from distutils import spawn
from PIL import Image

from nidaba import storage
from nidaba import uzn
from nidaba.config import nidaba_cfg
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaOcropusException
from nidaba.nidabaexceptions import NidabaPluginException


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


@app.task(base=NidabaTask, name=u'nidaba.ocr.ocropus')
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
                                   model))[0] + '.html'
    model = storage.get_abs_path(*(nidaba_cfg['ocropus_models'][model]))
    return storage.get_storage_path(ocr(input_path, output_path, model))



def ocr(image_path, segmentation_path, output_path, model_path):
    """
    Scan a single image with ocropus.

    Reads a single image file from ```imagepath``` and writes the recognized
    text as in hOCR format into output_path.

    Args:
        image_path (unicode): Path of the input file
        segmentation_path (unicode): Path of the segmentation .uzn file.
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
        network = ocrolib.load_object(model_path, verbose=0)
        lnorm = getattr(network, "lnorm")
    except Exception as e:
        raise NidabaOcropusException('Something somewhere broke: ' + e.msg)
    im = Image.open(image_path)
    w, h = im.size

    with open(segmentation_path, 'r') as seg_fp:
        doc = dominate.document()
        with doc.head:
            meta(name='ocr-system', content='ocropus')
            meta(name='ocr-capabilities', content='ocr_page ocr_line')
            meta(charset='utf-8')

        hocr_title = micro_hocr()
        hocr_title.add(u'bbox', 0, 0, str(w), str(h))
        hocr_title.add(u'image', image_path)

        with doc.add(div(cls='ocr_page', title=str(hocr_title))):
            for box in uzn.UZNReader(seg_fp):
                with span(cls='ocr_line') as line_span:
                    line_title = micro_hocr()
                    line_title.add(u'bbox', *box[:-1])
                    line_span['title'] = str(line_title)
                    line = ocrolib.pil2array(im.crop(box[:-1]))
                    temp = np.amax(line)-line
                    temp = temp*1.0/np.amax(temp)
                    lnorm.measure(temp)
                    line = lnorm.normalize(line,cval=np.amax(line))
                    if line.ndim == 3:
                        np.mean(line, 2)
                    line = ocrolib.lstm.prepare_line(line, 16)
                    pred = network.predictString(line)
                    pred = ocrolib.normalize_text(pred)
                    line_span.add(pred)

        with open(output_path, 'wb') as fp:
            fp.write(unicode(doc).encode('utf-8'))
    return output_path
