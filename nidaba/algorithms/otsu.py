"""
nidaba.algorithms.otsu
~~~~~~~~~~~~~~~~~~~~~~

Module implementing variants of Otsu's method.

"""

from __future__ import unicode_literals, print_function, absolute_import

import numpy as np


def otsu(im):
    """
    A naive native python implementation of Otsu thresholding (or at least the
    algorithm Wikipedia describes as Otsu's method).

    Args:
        im (PIL.Image): A PIL Image object in mode 'L' (8bpp grayscale)

    Returns:
        PIL.Image in mode '1' (1bpp b/w) containing the binarized image
    """

    assert im.mode == 'L'
    hist = im.histogram()
    total = np.prod(im.size)
    st = np.inner(range(0, len(hist)), hist)

    wb = 0.0
    sb = 0.0

    thresh = -1
    mvar = 0.0
    for i in range(0, len(hist)):
        wb += hist[i]
        if wb == 0:
            continue
        wf = total - wb
        if wf == 0:
            break
        sb += i * hist[i]
        mb = sb / wb
        mf = (st - sb) / wf
        bcv = wb * wf * (mb - mf) ** 2
        if bcv > mvar:
            mvar = bcv
            thresh = i

    return im.point(lambda p: p > thresh and 255, mode='1')
