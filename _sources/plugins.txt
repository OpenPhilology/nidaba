Plugins
=======

Tasks requiring extensive external or hard-to-install dependencies are
contained in plugins. Some plugins are shipped with the standard distribution
while others may be available from third parties. Prerequisites needed for
using each plugin are usually stated in its docstring.

Architecture
------------

Nidaba uses the `stevedore <http://docs.openstack.org/developer/stevedore/>`_
Python package for dynamic plugin management. It builds on top of `setuptools
entry points
<https://pythonhosted.org/setuptools/setuptools.html#dynamic-discovery-of-services-and-plugins>`_
enabling it to use plugins from any source as long as it has been installed
using setuptools. 

Plugins are located in the ``nidaba.plugins`` namespace and configured in the
``nidaba.yaml`` configuration file in the ``plugins_load`` section:

.. code-block:: yaml

   plugins_load:
     tesseract: {implementation: capi,
                 tessdata: /usr/share/tesseract-ocr}
     ocropus: {}
     kraken: {}
     leptonica: {}

Configuration data required by plugins can be stored in the dictionary beneath
the plugin name; after importing the module the setup function of the module
will be called with the corresponding configuration data.

Registering tasks requires getting access to the global application object of
celery. After importing it from ``nidaba.celery`` your tasks can be decorated
as usual. Remember that all tasks should derive from the
``nidaba.tasks.helper.NidabaTask`` object.

.. _builtin_plugins: 

Builtin Plugins
---------------

.. automodule:: nidaba.plugins.kraken

   .. autofunction:: nlbin(doc, method, threshold, zoom, escale, border, perc, range, low, high)
   .. autofunction:: segmentation_kraken(doc, method)
   .. autofunction:: ocr_kraken(doc, method, model)

.. automodule:: nidaba.plugins.ocropus

   .. autofunction:: ocr_ocropus(doc, method, model)

.. automodule:: nidaba.plugins.tesseract

   .. autofunction:: segmentation_tesseract(doc, method)
   .. autofunction:: ocr_tesseract(doc, method, languages)

.. automodule:: nidaba.plugins.leptonica

   .. autofunction:: sauvola(doc, method, whsize, factor)
   .. autofunction:: dewarp(doc, method)
   .. autofunction:: deskew(doc, method)
