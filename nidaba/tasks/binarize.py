# -*- coding: utf-8 -*-
"""
nidaba.tasks.binarize
~~~~~~~~~~~~~~~~~~~~~

Tasks for segmentation of color images into binary images. More often than not
these will operate on grayscale input.
"""

from __future__ import absolute_import, unicode_literals

from nidaba import storage
from nidaba import leper
from nidaba import kraken
from nidaba.nidabaexceptions import NidabaInvalidParameterException
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask

import re

@app.task(base=NidabaTask, name=u'nidaba.binarize.nlbin')
def nlbin(doc, id, method=u'nlbin', threshold=0.5, zoom=0.5, escale=1.0,
          border=0.1, perc=80, range=20, low=5, high=90):
    """
    Binarizes an input document utilizing ocropus'/kraken's nlbin algorithm.

    Args:
        doc (unicode, unicode): The input document tuple.
        id (unicode): The nidaba batch identifier this task is a part of
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
    if (1 > perc > 100) or (1 > low > 100) or (1 > high > 100):
        raise NidabaInvalidParameterException('Parameters (' + unicode(perc) +
                                              ',' + unicode(low) + ',' +
                                              unicode(high) + ',' +
                                              'outside of valid range')
    print(output_path)
    return storage.get_storage_path(kraken.nlbin(input_path, output_path,
                                                 threshold, zoom, escale,
                                                 border, perc, range, low,
                                                 high))

@app.task(base=NidabaTask, name=u'nidaba.binarize.otsu')
def otsu(doc, id, method=u'otsu', thresh=100, mincount=50, bgval=255,
         smoothx=2, smoothy=2):
    """
    Binarizes an input document utilizing leptonicas modified Otsu thresholding
    incorporating a background normalization as a preprocessing step.

    Args:
        doc (unicode, unicode): The input document tuple.
        id (unicode): The nidaba batch identifier this task is a part of
        method (unicode): The suffix string appended to all output files.
        thresh (int): Threshold for background normalization.
        mincount (int): Min threshold on background counts in a tile.
        bgval (int): Target background value. Typically 255. Valid >0.
        smoothx (int): Half-width of block convolution kernel width. Valid >= 0
        smoothy (int):  Half-width of block convolution kernel height. Valid >=
                        0

    Returns:
        (unicode, unicode): Storage tuple of the output file

    Raises:
        NidabaInvalidParameterException: Input parameters are outside the valid
                                         range.

    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method, unicode(thresh),
                                        unicode(mincount), unicode(bgval),
                                        unicode(smoothx), unicode(smoothy))
    if smoothx < 0 or smoothy < 0 or bgval < 0 or thresh < 0 or mincount < 0:
        raise NidabaInvalidParameterException('Parameters (' + unicode(thresh)
                                              + ',' + unicode(mincount) + ',' +
                                              unicode(bgval) + ',' +
                                              unicode(smoothx) + ',' +
                                              unicode(smoothy) + ',' +
                                              ') outside of valid range')
    return storage.get_storage_path(leper.otsu_binarize(input_path,
                                                        output_path, thresh,
                                                        mincount, bgval,
                                                        smoothx, smoothy))


@app.task(base=NidabaTask, name=u'nidaba.binarize.sauvola')
def sauvola(doc, id, method=u'sauvola', whsize=10, factor=0.35):
    """
    Binarizes an input document utilizing Sauvola thresholding as described in
    [0]. Expects 8bpp grayscale images as input.

    [0] Sauvola, Jaakko, and Matti Pietikäinen. "Adaptive document image
    binarization." Pattern recognition 33.2 (2000): 225-236.

    Args:
        doc (unicode): The input document tuple.
        id (unicode): The nidaba batch identifier this task is a part of
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
