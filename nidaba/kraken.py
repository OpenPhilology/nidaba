"""
nidaba.kraken
~~~~~~~~~~~~~

Routines encapsulating the kraken OCR engine
"""

from __future__ import absolute_import

from PIL import Image

from kraken import binarization


def nlbin(imagepath, resultpath, threshold=0.5, zoom=0.5, escale=1.0,
          border=0.1, perc=80, range=20, low=5, high=90):
    """
    Converts an 8bpp grayscale image into a black and white one using the
    non-linear processing algorithm from ocropus/kraken.

    Args:
        imagepath: Path of the input image
        resultpath: Path of the output image
        threshold (float):
        zoom (float):
        escale (float):
        border (float):
        perc (int):
        range (int):
        low (int):
        high (int):

    Returns:
        unicode: Path of the output file
    """
    img = Image.open(imagepath)
    binarization.nlbin(img, threshold, zoom, escale, border, perc, range, low,
                       high).save(resultpath)
    return resultpath
