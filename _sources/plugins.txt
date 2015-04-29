Plugins
=======

Tasks requiring external dependencies which are not installabe using Python
utilities are separated into plugins. Plugins can be selected in the
configuration file. 

.. automodule:: nidaba.plugins.kraken

   .. autofunction:: ocr_kraken(doc, method, model)

.. automodule:: nidaba.plugins.ocropus

   .. autofunction:: ocr_ocropus(doc, method, model)

.. automodule:: nidaba.plugins.tesseract

   .. autofunction:: ocr_tesseract(doc, method, languages)

.. automodule:: nidaba.plugins.leptonica

   .. autofunction:: sauvola(doc, method, whsize, factor)
   .. autofunction:: dewarp(doc, method)
   .. autofunction:: deskew(doc, method)
