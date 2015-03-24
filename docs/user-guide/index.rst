:title: User Guide
:description: Learn how to install and use nidaba

.. _installing_nidaba:

Installation
============

At least for testing purposes it is recommended to install nidaba into a virtualenv. 

.. _external_dependencies:

Installing External Dependencies
--------------------------------

While nidaba itself is mostly written in python there are some external
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


Installing from PyPi
--------------------

Execute: 

.. code-block:: console

        $ pip install nidaba

and you're done.

Installing from Source
----------------------

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

.. _configuring_nidaba:

Configuration
=============

There are currently two configuration files, one used by the celery framework
and one containing the actual nidaba configuration. Both are written in `YAML
<http://www.yaml.org>`_ so indentation and whitespace is important. They are
installed automatically into sys.prefix/etc/nidaba/{celery,nidaba}.yaml; usually
into the root of the virtualenv containing nidaba or /usr/etc/nidaba/.

The former resembles a `celery configuration object
<http://celery.readthedocs.org/en/latest/configuration.html>`_ and may contain
all available options. The example file looks like this::

	BROKER_URL: 'redis://127.0.0.1:6379'
	CELERY_RESULT_BACKEND: 'redis://127.0.0.1:6379'
	CELERY_TASK_SERIALIZER: 'json'
	CELERY_RESULT_SERIALIZER: 'json'

The later contains essential configuration for several subtasks and the overall
framework::

	storage_path: ~/OCR
	lang_dicts:
	  polytonic_greek: [dicts, greek.dic]
	  lojban: [dicts, lojban.dic]
	  german: [dicts, german.dic]
	old_tesseract: n
	old_ocropus: n
	ocropus_models:
	  greek: [models, greek.pyrnn.gz]
	  atlantean: [models, atlantean.pyrnn.gz]
	  fraktur: [models, fraktur.pyrnn.gz]
	  fancy_ligatures: [models, ligatures.pyrnn.gz]

storage_path
        The home directory for nidaba to store files created by OCR jobs, i.e.
        the location of the shared storage medium. This may differ on
        different machines in the cluster.

lang_dicts
	A list of mappings from unique identifiers to storage tupels where a
	tupel is of the format [directory, path] resulting in the absolute path
	storage_path/directory/path. Each mapping defines a dictionary that can
	be utilized by the spell checker and other tasks utilizing dictionaries.


old_tesseract
        A switch for the tesseract hOCR output format. Set to True if your
        tesseract produces hOCR output with an .html extension.

old_ocropus
	Legacy ocropus versions don't have some command line switches which are
	required for operation with more recent ones. If you're not running ocropus
	from github.com/tmbdev or ocropus-gpageseg does not have a --nocheck option set
	this to yes.

ocropus_models
	A list of mappings from unique identifiers to storage tupels where a
	tupel is of the format [directory, path] resulting in the absolute path
	storage_path/directory/path. Each mapping defines a single neuronal
	network available to the ocropus OCR task. These have to exist on all
	machines running nidaba and therefore have to be on the common storage medium
	beneath storage_path.

.. _installing_nidaba_intro:

Quick Start
===========

.. _preparing_celery:

Running the celery worker server
--------------------------------

Starting the celery worker server is quite simple and the only requirement is
that it is NOT run inside the nidaba directory and the message broker is up and
running:

.. code-block:: console

	$ celery -A nidaba.tasks worker

For further worker server options have a look at `celery`_.

.. _`celery`: https://celery.readthedocs.org/en/latest/

.. _using_cli:

The Command Line Interface
--------------------------

The simplest way to put jobs into the pipeline is using the nidaba command line
utility. It is automatically installed during the installation procedure.

.. _cli_config:

nidaba config
~~~~~~~~~~~~~

The *config* subcommand is used to inspect the current nidabaconfig.py:

.. code-block:: console

        $ nidaba config
        * LANG_DICTS
        {u'german': (u'dicts', u'test/german.txt'),
         u'lojban': (u'dicts', u'test/lojban.txt'),
         u'polytonic_greek': (u'dicts', u'greek.dic')}
        * OCROPUS_MODELS
        {u'atlantean': (u'models', u'atlantean.pyrnn.gz'),
         u'fraktur': (u'models', u'fraktur.pyrnn.gz'),
         u'greek': (u'models', u'greek.pyrnn.gz')}
        * OLD_TESSERACT
        False
        * STORAGE_PATH
        u'~/OCR'

.. _cli_batch:

nidaba batch
~~~~~~~~~~~~

The *batch* subcommand is used to create a job for the pipeline. A rather
minimal invocation looks like this:

.. code-block:: console

        $ nidaba batch --binarize "sauvola:whsize=10;whsize=20;whsize=30;whsize=40,factor=0.6" --ocr tesseract:eng -- ./input.tiff
        35be45e9-9d6d-47c7-8942-2717f00f84cb

It converts the input file *input.tiff* to grayscale, binarizes it using the
Sauvola algorithm with 4 different window sizes, and finally runs it through
tesseract with the English language model.

--binarize
        Defines the binarization parameters. It consists of a list of terms in
        the format algorithm1:arg1=a,arg2=b;arg1=n algorithm2:arg1=1;arg1=2;...
        where algorithm is one of the algorithms implemented and args are their
        configuration parameters. Have a look at :mod:`nidaba.tasks.binarize`
        for possible values.

--ocr
        A list of OCR engine options in the format engine:lang1,lang2,lang3
        engine2:model... where engine is either *tesseract* or *ocropus* and
        lang is a tesseract language model and model is an ocropus model
        previously defined in nidabaconfig.
--willitblend
        Blends all output hOCR files into a single hOCR document using the
        dummy scoring algorithm.
--grayscale
        A switch to indicate that input files are already 8bpp grayscale and
        conversion to grayscale is unnecessary.

.. _cli_status:

nidaba status
~~~~~~~~~~~~~

The *status* subcommand is used to check the status of a job. It requires the
return value of the *nidaba batch* command.

A currently running job will return PENDING:

.. code-block:: console
        
        $ nidaba status 35be45e9-9d6d-47c7-8942-2717f00f84cb
        PENDING

When the job has been processed the status command will return a list of paths
containing the final output:

.. code-block:: console
        
        $ nidaba status 35be45e9-9d6d-47c7-8942-2717f00f84cb
        SUCCESS
                /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_10_0.3_ocr_tesseract_eng.tiff.hocr
                /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_20_0.3_ocr_tesseract_eng.tiff.hocr
                /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_30_0.3_ocr_tesseract_eng.tiff.hocr
                /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_40_0.3_ocr_tesseract_eng.tiff.hocr

On failure the subtasks that failed and their error message will be printed:

.. code-block:: console

        $ nidaba status 35be45e9-9d6d-47c7-8942-2717f00f84cb
        FAILURE
                rgb_to_gray: Color blindness not found


.. _using_webfrontend:

The Web Interface
-----------------

Not implemented yet.
