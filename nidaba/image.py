"""
nidaba.image
~~~~~~~~~~~~

Common image processing functions encapsulating the PIL or pythonica image
interface to absolute file paths.
"""

from __future__ import absolute_import

from PIL import Image

import nidaba.algorithms.otsu


def otsu(imagepath, resultpath):
    """
    Binarizes an grayscale image using Otsu's algorithm.

    Arguments:
        imagepath: Path of the input image
        resultpath: Path of the output image

    Returns:
        unicode: Path of the actual output file
    """

    im = Image.open(imagepath)
    nidaba.algorithms.otsu.otsu(im).save(resultpath)
    return resultpath


def rgb_to_gray(imagepath, resultpath):
    """
    Converts an RGB or CMYK image into a 8bpp grayscale image.

    Arguments:
        imagepath: Path of the input image
        resultpath: Path of the output image

    Returns:
        unicode: Path of the actual output file
    """

    img = Image.open(imagepath)
    img.convert('L').save(resultpath)
    return resultpath
