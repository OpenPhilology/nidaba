# -*- coding: utf-8 -*-
"""
nidaba.plugins.leptonica
~~~~~~~~~~~~~~~~~~~~~~~~

Plugin for leptonica functions provided through leper
"""

from __future__ import absolute_import

import re

from nidaba import leper
from nidaba import storage

from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaInvalidParameterException


@app.task(base=NidabaTask, name=u'nidaba.binarize.sauvola')
def sauvola(doc, method=u'sauvola', whsize=10, factor=0.35):
    """
    Binarizes an input document utilizing Sauvola thresholding as described in
    [0]. Expects 8bpp grayscale images as input.

    [0] Sauvola, Jaakko, and Matti Pietikäinen. "Adaptive document image
    binarization." Pattern recognition 33.2 (2000): 225-236.

    Args:
        doc (unicode): The input document tuple.
        method (unicode): The suffix string appended to all output files
        whsize (int): The window width and height that local statistics are
                      calculated on are twice the value of whsize. The minimal
                      value is 2.
        factor (float): The threshold reduction factor due to variance. 0 =<
                        factor < 1.

    Returns:
        (unicode, unicode): Storage tuple of the output file

    Raises:
        NidabaInvalidParameterException: Input parameters are outside the valid
                                         range.
    """
    input_path = storage.get_abs_path(*doc)
    if whsize < 2 or factor >= 1.0 or factor < 0:
        raise NidabaInvalidParameterException('Parameters (' + unicode(whsize)
                                              + ',' + unicode(factor) +
                                              ') outside of valid range')
    output_path = storage.insert_suffix(input_path, method, unicode(whsize),
                                        re.sub(ur'[^0-9]', u'',
                                               unicode(factor)))
    return storage.get_storage_path(leper.sauvola_binarize(input_path,
                                                           output_path, whsize,
                                                           factor))


@app.task(base=NidabaTask, name=u'nidaba.img.dewarp')
def dewarp(doc, method=u'dewarp'):
    """
    Removes perspective distortion (as commonly exhibited by overhead scans)
    from an 1bpp input image.

    Args:
        doc (unicode, unicode): The input document tuple.
        method (unicode): The suffix string appended to all output files.

    Returns:
        (unicode, unicode): Storage tuple of the output file
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method)
    return storage.get_storage_path(leper.dewarp(input_path, output_path))


@app.task(base=NidabaTask, name=u'nidaba.img.deskew')
def deskew(doc, method=u'deskew'):
    """
    Removes skew (rotational distortion) from an 1bpp input image.

    Args:
        doc (unicode, unicode): The input document tuple.
        method (unicode): The suffix string appended to all output files.

    Returns:
        (unicode, unicode): Storage tuple of the output file
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method)
    return storage.get_storage_path(leper.deskew(input_path, output_path))
