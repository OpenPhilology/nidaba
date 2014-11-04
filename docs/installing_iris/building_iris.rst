:title: Installing the Iris pipeline
:description: Learn how to install the Iris pipeline

.. _building_iris:

Building the Iris pipeline
==========================

At least for testing purposes it is recommended to install Iris into a virtualenv.

.. _external_dependencies:

Installing external dependencies
--------------------------------

While Iris itself is mostly written in python there are some external
dependencies. The first set is required in all use cases, while the second one
can be adapted for particular requirements.

First are the required packages for building various python packages as numpy
and lxml and the leptonica C wrapper. 

.. code-block:: console

        # apt-get install python python-dev build-essential libxml2-dev libxslt1-dev libleptonica-dev 

leptonica's API is not stable across versions, for the current version of
leper, the leptonica wrapper, to build a version >=1.70 is required.

Next we'll have to install some actual OCR engines and some language models. To
run the unit tests at least the ancient greek language model is required:

.. code-block:: console

        # apt-get install tesseract-ocr tesseract-ocr-grc

Further ocropus may be installed; this varies by distribution.

.. _configuring_iris:

Configuration
-------------

There are currently two configuration files that have to be edited before
installation. irisconfig.py and celeryconfig.py. Celeryconfig is a standard
`celery configuration object
<http://celery.readthedocs.org/en/latest/configuration.html>` and may look like
this::

        BROKER_URL = 'redis://127.0.0.1:6379'
        CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379'
        CELERY_TASK_SERIALIZER = 'json'
        CELERY_RESULT_SERIALIZER = 'json'
        CELERY_TIMEZONE = 'Europe/Berlin'
        CELERY_ENABLE_UTC = True

Irisconfig contains essential configuration for the pipeline as a whole and
some subtasks::

        STORAGE_PATH = u'~/OCR'
        LANG_DICTS = { u'polytonic_greek': (u'dicts', u'greek.dic'), 
                       u'lojban': (u'dicts', u'test/lojban.txt'), 
                       u'german': (u'dicts', u'test/german.txt')}
        OLD_TESSERACT = False
        OCROPUS_MODELS = { u'greek': (u'models', u'greek.pyrnn.gz'),
                           u'atlantean': (u'models', u'atlantean.pyrnn.gz'),
                           u'fraktur': (u'models', u'fraktur.pyrnn.gz')}

STORAGE_PATH
        The home directory for Iris to store files created by OCR jobs, i.e.
        the location of the shared storage medium. This may be different on
        different machines in the cluster.

LANG_DICTS
        A python dictionary mapping languages to storage tupels where a tupel
        is of the format (directory, path) resulting in the absolute path
        STORAGE_PATH/directory/path. Each item contains a spell checker
        dictionary for a single language.

OLD_TESSERACT
        A switch for the tesseract hOCR output format. Set to True if your
        tesseract produces hOCR output with an .html extension.

OCROPUS_MODELS
        A python dictionary mapping identifiers to storage tupels where a tupel
        is of the format (directory, path) resulting in the absolute path
        STORAGE_PATH/directory/path. Each item contains a single ocropus
        neuronal network.

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
