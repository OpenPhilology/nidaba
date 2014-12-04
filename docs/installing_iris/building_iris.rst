:title: Installing the Iris pipeline
:description: Learn how to install the Iris pipeline

.. _building_iris:

Building the Iris Pipeline
==========================

At least for testing purposes it is recommended to install Iris into a virtualenv. 

.. _external_dependencies:

Installing External Dependencies
--------------------------------

While Iris itself is mostly written in python there are some external
dependencies. The first set is required in all use cases, while the second one
can be adapted for particular requirements.

First are the required packages for building various python packages as numpy
and lxml and the leptonica C wrapper. 

.. code-block:: console

        # apt-get install python python-dev build-essential libxml2-dev libxslt1-dev libleptonica-dev 

leptonica's API is not stable across versions, for the current version of
leper, the leptonica wrapper, to compile a version >=1.70 is required.

Next we'll have to install some actual OCR engines and language models. To
run the unit tests at least the ancient greek language model is required:

.. code-block:: console

        # apt-get install tesseract-ocr tesseract-ocr-grc

Further ocropus may be installed; the process varies by distribution.

.. _installing_iris:

Installing Iris
---------------

If you want to install from source, ensure you have `pip`_ installed and run:

.. code-block:: console

        $ pip install .

There are some miscellaneous models and dictionaries not packaged with the
source code. To download these run:

.. code-block:: console

        $ python setup.py download

Afterwards the test suite can be run:

.. code-block:: console

        $ python setup.py test

.. _`pip`: https://pip.pypa.io/en/latest/
