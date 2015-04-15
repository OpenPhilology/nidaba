nidaba.tasks package
====================

Submodules
----------

nidaba.tasks.binarize module
----------------------------

.. automodule:: nidaba.tasks.binarize
    :members:
    :undoc-members:
    :show-inheritance:

    .. autofunction:: nlbin(doc, method, threshold, zoom, escale, border, perc, range, low, high)
    .. autofunction:: otsu(doc, method, thresh, mincount, bgval, smoothx, smoothy)
    .. autofunction:: sauvola(doc, method, whsize, factor)

nidaba.tasks.helper module
--------------------------

.. automodule:: nidaba.tasks.helper
    :members:
    :undoc-members:
    :show-inheritance:

nidaba.tasks.img module
-----------------------

.. automodule:: nidaba.tasks.img
    :members:
    :undoc-members:
    :show-inheritance:

    .. autofunction:: rgb_to_gray(doc, method)
    .. autofunction:: dewarp(doc, method)
    .. autofunction:: deskew(doc, method)

nidaba.tasks.ocr module
-----------------------

.. automodule:: nidaba.tasks.ocr
    :members:
    :undoc-members:
    :show-inheritance:

    .. autofunction:: ocr_tesseract(doc, method, languages)
    .. autofunction:: ocr_ocropus(doc, method, model)

nidaba.tasks.util module
------------------------

.. automodule:: nidaba.tasks.util
    :members:
    :undoc-members:
    :show-inheritance:

    .. autofunction:: blend_hocr(doc, language, method)
    .. autofunction:: sync(doc)

Module contents
---------------

.. automodule:: nidaba.tasks
    :members:
    :undoc-members:
    :show-inheritance:
