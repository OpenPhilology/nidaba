# -*- coding: utf-8 -*-
"""
nidaba.tasks.img
~~~~~~~~~~~~~~~~

Some general image processing tasks that are outside the scope of more specific
packages (e.g. binarization).

"""

from __future__ import absolute_import, unicode_literals

from nidaba import storage
from nidaba import leper
from nidaba import image
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask


@app.task(base=NidabaTask, name=u'nidaba.img.rgb_to_gray')
def rgb_to_gray(doc, method=u'rgb_to_gray'):
    """
    Converts an arbitrary bit depth image to grayscale and writes it back
    appending a suffix.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files.

    Returns:
        (unicode, unicode): Storage tuple of the output file
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method)
    return storage.get_storage_path(image.rgb_to_gray(input_path, output_path))


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
