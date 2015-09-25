# -*- coding: utf-8 -*-
"""
nidaba.plugins.leptonica
~~~~~~~~~~~~~~~~~~~~~~~~

Plugin accessing `leptonica <http://leptonica.com>`_ functions.

This plugin requires a liblept shared object in the current library search
path. On Debian-based systems it can be installed using apt-get

.. code-block:: console

    # apt-get install libleptonica-dev

Leptonica's APIs are rather unstable and may differ significantly between
versions. If this plugin fails with weird error messages or workers are just
dying without discernable cause please submit a bug report including your
leptonica version.
"""

from __future__ import unicode_literals, print_function, absolute_import

import ctypes

from nidaba import storage

from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import (NidabaInvalidParameterException,
                                     NidabaLeptonicaException,
                                     NidabaPluginException)

leptlib = 'liblept.so'


def setup(*args, **kwargs):
    try:
        ctypes.cdll.LoadLibrary(leptlib)
    except Exception as e:
        raise NidabaPluginException(e.message)


@app.task(base=NidabaTask, name=u'nidaba.binarize.sauvola',
          arg_values={'whsize': 'int', 'factor': (0.0, 1.0)})
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
    output_path = storage.insert_suffix(input_path, method, unicode(whsize),
                                        unicode(factor))
    lept_sauvola(input_path, output_path, whsize, factor)
    return storage.get_storage_path(output_path)


def lept_sauvola(image_path, output_path, whsize=10, factor=0.35):
    """
    Binarizes an input document utilizing Sauvola thresholding as described in
    [0]. Expects 8bpp grayscale images as input.

    [0] Sauvola, Jaakko, and Matti Pietikäinen. "Adaptive document image
    binarization." Pattern recognition 33.2 (2000): 225-236.

    Args:
        image_path (unicode): Input image path
        output_path (unicode): Output image path
        whsize (int): The window width and height that local statistics are
                      calculated on are twice the value of whsize. The minimal
                      value is 2.
        factor (float): The threshold reduction factor due to variance. 0 =<
                        factor < 1.

    Raises:
        NidabaInvalidParameterException: Input parameters are outside the valid
                                         range.
    """

    if whsize < 2 or factor >= 1.0 or factor < 0:
        raise NidabaInvalidParameterException('Parameters (' + unicode(whsize)
                                              + ',' + unicode(factor) +
                                              ') outside of valid range')
    try:
        lept = ctypes.cdll.LoadLibrary(leptlib)
    except OSError as e:
        raise NidabaLeptonicaException('Loading leptonica failed: ' +
                                       e.message)
    pix = ctypes.c_void_p(lept.pixRead(image_path.encode('utf-8')))
    opix = ctypes.c_void_p()
    if lept.pixGetDepth(pix) != 8:
        lept.pixDestroy(ctypes.byref(pix))
        raise NidabaLeptonicaException('Input image is not grayscale')
    if lept.pixSauvolaBinarize(pix, whsize, ctypes.c_float(factor), 0, None,
                               None, None, ctypes.byref(opix)):
        lept.pixDestroy(ctypes.byref(pix))
        raise NidabaLeptonicaException('Binarization failed for unknown '
                                       'reason.')
    if lept.pixWriteImpliedFormat(output_path.encode('utf-8'), opix, 100, 0):
        lept.pixDestroy(ctypes.byref(pix))
        lept.pixDestroy(ctypes.byref(pix))
        raise NidabaLeptonicaException('Writing binarized PIX failed')
    lept.pixDestroy(ctypes.byref(opix))
    lept.pixDestroy(ctypes.byref(pix))


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
    lept_dewarp(input_path, output_path)
    return storage.get_storage_path(output_path)


def lept_dewarp(image_path, output_path):
    """
    Removes perspective distortion from an 1bpp input image.

    Args:
        image_path (unicode): Path to the input image
        output_path (unicode): Path to the output image

    Raises:
        NidabaLeptonicaException if one of leptonica's functions failed.
    """
    try:
        lept = ctypes.cdll.LoadLibrary(leptlib)
    except OSError as e:
        raise NidabaLeptonicaException('Loading leptonica failed: ' +
                                       e.message)
    pix = ctypes.c_void_p(lept.pixRead(image_path.encode('utf-8')))
    opix = ctypes.c_void_p()
    ret = lept.dewarpSinglePage(pix, 0, 1, 1, ctypes.byref(opix), None, 0)
    if ret == 1 or ret is None:
        lept.pixDestroy(ctypes.byref(pix))
        lept.pixDestroy(ctypes.byref(opix))
        raise NidabaLeptonicaException('Dewarping failed for unknown reason.')
    if lept.pixWriteImpliedFormat(output_path.encode('utf-8'), opix, 100, 0):
        lept.pixDestroy(ctypes.byref(pix))
        lept.pixDestroy(ctypes.byref(opix))
        raise NidabaLeptonicaException('Writing dewarped PIX failed')
    lept.pixDestroy(ctypes.byref(pix))
    lept.pixDestroy(ctypes.byref(opix))


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
    lept_deskew(input_path, output_path)
    return storage.get_storage_path(output_path)


def lept_deskew(image_path, output_path):
    """
    Removes skew (rotational distortion from an 1bpp input image.

    Args:
        image_path (unicode): Input image
        output_path (unicode): Path to the output document

    Raises:
        NidabaLeptonicaException if one of leptonica's functions failed.
    """
    try:
        lept = ctypes.cdll.LoadLibrary(leptlib)
    except OSError as e:
        raise NidabaLeptonicaException('Loading leptonica failed: ' +
                                       e.message)
    pix = ctypes.c_void_p(lept.pixRead(image_path.encode('utf-8')))
    opix = ctypes.c_void_p(lept.pixFindSkewAndDeskew(pix, 4, None, None))
    if opix is None:
        lept.pixDestroy(ctypes.byref(pix))
        raise NidabaLeptonicaException('Deskewing failed for unknown reason.')
    if lept.pixWriteImpliedFormat(output_path.encode('utf-8'), opix, 100, 0):
        lept.pixDestroy(ctypes.byref(pix))
        lept.pixDestroy(ctypes.byref(opix))
        raise NidabaLeptonicaException('Writing deskewed PIX failed')
    lept.pixDestroy(ctypes.byref(pix))
    lept.pixDestroy(ctypes.byref(opix))
