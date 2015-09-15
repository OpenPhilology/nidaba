# -*- coding: utf-8 -*-
"""
nidaba.tasks.binarize
~~~~~~~~~~~~~~~~~~~~~

Tasks for segmentation of color images into binary images. More often than not
these will operate on grayscale input.
"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba import storage
from nidaba import image
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask


@app.task(base=NidabaTask, name=u'nidaba.binarize.otsu')
def otsu(doc, method=u'otsu'):
    """
    Binarizes an input document utilizing a naive implementation of Otsu's
    thresholding.

    Args:
        doc (unicode, unicode): The input document tuple.
        method (unicode): The suffix string appended to all output files.

    Returns:
        (unicode, unicode): Storage tuple of the output file

    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method)
    return storage.get_storage_path(image.otsu(input_path, output_path))
