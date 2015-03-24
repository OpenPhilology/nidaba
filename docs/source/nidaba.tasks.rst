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

    .. autofunction:: otsu(doc, id, method, thresh, mincount, bgval, smoothx, smoothy)
    .. autofunction:: sauvola(doc, id, method, whsize, factor)

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

    .. autofunction:: rgb_to_gray(doc, id method)
    .. autofunction:: dewarp(doc, id, method)
    .. autofunction:: deskew(doc, id, method)

nidaba.tasks.ocr module
-----------------------

.. automodule:: nidaba.tasks.ocr
    :members:
    :undoc-members:
    :show-inheritance:

    .. autofunction:: ocr_tesseract(doc, id, method, languages)
    .. autofunction:: ocr_ocropus(doc, id, method, model)

nidaba.tasks.util module
------------------------

.. automodule:: nidaba.tasks.util
    :members:
    :undoc-members:
    :show-inheritance:

    .. autofunction:: blend_hocr(docs, id, language, method)
    .. autofunction:: sync(arg)

Module contents
---------------

.. automodule:: nidaba.tasks
    :members:
    :undoc-members:
    :show-inheritance:
