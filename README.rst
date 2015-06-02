Overview
========

.. image:: https://travis-ci.org/OpenPhilology/nidaba.svg
        :target: https://travis-ci.org/OpenPhilology/nidaba

Nidaba is the central controller for the entire OGL OCR pipeline. It oversees
and automates the process of converting raw images into citable collections of
digitized texts.

It offers the following functionality:

- Grayscale Conversion
- Binarization utilizing `Sauvola
  <http://www.mediateam.oulu.fi/publications/pdf/24.p>`__ adaptive
  thresholding, Otsu, or ocropus's nlbin algorithm
- Deskewing
- Dewarping
- Integration of `tesseract <http://code.google.com/p/tesseract-ocr/>`_,
  `kraken <http://mittagessen.github.io/kraken>`_, and `ocropus
  <http://github.com/tmbdev/ocropy>`_ OCR engines
- Various postprocessing utilities like spell-checking, merging of multiple
  results, and ground truth comparison.

As it is designed to use a common storage medium on network attached storage
and the `celery <http://celeryproject.org>`__ distributed task queue it scales
nicely to multi-machine clusters.

Build
=====

To easiest way to install the latest stable(-ish) nidaba is from PyPi:

::

    $ pip install nidaba

or run:

::

    $ pip install .

in the git repository for the bleeding edge development version.

Some useful tasks have external dependencies. A good start is:

::

    # apt-get install libtesseract3 tesseract-ocr-eng libleptonica-dev liblept

Tests
=====

Per default no dictionaries and OCR models necessary to runs the tests are
installed. To download the necessary files run:

::

    $ python setup.py download

::

    $ python setup.py nosetests

Tests for modules that call external programs, at the time only tesseract,
ocropus, and kraken, will be skipped if these aren't installed.

Running
=======

First edit (the installed) nidaba.yaml and celery.yaml to fit your needs. Have
a look at the `docs <https:///mittagessen.github.io/nidaba>`__ if you haven't
set up a celery-based application before.

Then start up the celery daemon with something like:

::

    $ celery -A nidaba worker

Next jobs can be added to the pipeline using the nidaba executable:

::

    $ nidaba batch -b otsu -o tesseract:eng -- ./input.tiff
    Preparing filestore             [✓]
    Building batch                  [✓]
    951c57e5-f8a0-432d-8d77-8a2e27fff53c

Using the return code the current state of the job can be retrieved:

::

    $ nidaba status 25d79a54-9d4a-4939-acb6-8e168d6dbc7c
    PENDING

When the job has been processed the status command will return a list of paths
containing the final output:

::

    $ nidaba status 951c57e5-f8a0-432d-8d77-8a2e27fff53c
    SUCCESS
    14.tif → .../input_img.rgb_to_gray_binarize.otsu_ocr.tesseract_grc.tif.hocr

Documentation
=============

Want to learn more? `Read the
Docs <https:///openphilology.github.io/nidaba/>`__
