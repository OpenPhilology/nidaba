# -*- coding: utf-8 -*-
"""
nibada.tasks.binarize
~~~~~~~~~~~~~~~~~~~

Tasks for segmentation of color images into binary images. More often than not
these will operate on grayscale input. 
"""

from __future__ import absolute_import, unicode_literals

from nibada import storage
from nibada import leper
from nibada.celery import app
from nibada.tasks.helper import NibadaTask

import re

@app.task(base=NibadaTask, name=u'nibada.binarize.otsu')
def otsu(doc, id, method=u'binarize', thresh=100, mincount=50, bgval=255,
        smoothx=2, smoothy=2):
    """
    Binarizes an input document utilizing leptonicas modified Otsu thresholding
    incorporating a background normalization as a preprocessing step.

    Args:
        doc (unicode, unicode): The input document tuple.
        id (unicode): The nibada batch identifier this task is a part of
        method (unicode): The suffix string appended to all output files.
        thresh (int): Threshold for background normalization. 
        mincount (int): Min threshold on background counts in a tile.
        bgval (int): Target background value. Typically 255. Valid >0.
        smoothx (int): Half-width of block convolution kernel width. Valid >= 0
        smoothy (int):  Half-width of block convolution kernel height. Valid >= 0

    Returns:
        (unicode, unicode): Storage tuple of the output file

    Raises:
        NibadaInvalidParameterException: Input parameters are outside the valid
        range.

    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method, unicode(thresh),
            unicode(mincount), unicode(bgval), unicode(smoothx),
            unicode(smoothy))
    if smoothx < 0 or smoothy < 0 or bgval < 0 or thresh < 0 or mincount < 0:
        raise NibadaInvalidParameterException('Parameters (' + 
                                            unicode(thresh) + ',' +
                                            unicode(mincount) + ',' +
                                            unicode(bgval) + ',' +
                                            unicode(smoothx) + ',' + 
                                            unicode(smoothy) + ',' +
                                            ') outside of valid range')
    return storage.get_storage_path(leper.otsu_binarize(input_path,
        output_path, thresh, mincount, bgval, smoothx, smoothy))

        
@app.task(base=NibadaTask, name=u'nibada.binarize.sauvola')
def sauvola(doc, id, method=u'sauvola', whsize=10, factor=0.35):
    """
    Binarizes an input document utilizing Sauvola thresholding as described in
    [0]. Expects 8bpp grayscale images as input.

    [0] Sauvola, Jaakko, and Matti Pietikäinen. "Adaptive document image
    binarization." Pattern recognition 33.2 (2000): 225-236.
    
    Args:
        doc (unicode): The input document tuple.
        id (unicode): The nibada batch identifier this task is a part of
        method (unicode): The suffix string appended to all output files
        whsize (int): The window width and height that local statistics are
        calculated on are twice the value of whsize. The minimal value is 2.
        factor (float): The threshold reduction factor due to variance. 0 =<
        factor < 1.

    Returns:
        (unicode, unicode): Storage tuple of the output file

    Raises:
        NibadaInvalidParameterException: Input parameters are outside the valid
        range.
    """
    input_path = storage.get_abs_path(*doc)
    if whsize < 2 or factor >= 1.0 or factor < 0:
        raise NibadaInvalidParameterException('Parameters (' + unicode(whsize)
                + ',' + unicode(factor) + ') outside of valid range')
    output_path = storage.insert_suffix(input_path, method, unicode(whsize),
            re.sub(ur'[^0-9]', u'', unicode(factor)))
    return storage.get_storage_path(leper.sauvola_binarize(input_path,
        output_path, whsize, factor))
