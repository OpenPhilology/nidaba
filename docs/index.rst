Nidaba
======

Nidaba is an open source distributed optical character recognition pipeline
that makes it easy to preprocess, OCR, and postprocess scans of text documents
in a multitude of ways.

Nidaba is a powerful tool allowing you to mix and combine some of the most
advanced free image processing and character recognition software and
distribute the execution of this software to multiple machines.

.. toctree::
        :hidden:
        :maxdepth: 2

        Plugins <plugins>
        FAQs <faq>
        API Docs <source/modules>

Nidaba does a bunch of things for you:

        - `Grayscale Conversion <http://pillow.readthedocs.org/en/latest/reference/Image.html#PIL.Image.Image.convert>`_
        - `Binarization <http://en.wikipedia.org/wiki/Thresholding_%28image_processing%29>`_
        - `Deskewing <http://www.leptonica.com/skew-measurement.html>`_
        - `Dewarping <http://www.leptonica.com/dewarping.html>`_
        - `OCR <http://en.wikipedia.org/wiki/Optical_character_recognition>`_
        - Output merging

.. _installation:

Installation
============

Unless you are installing from a precompiled source you will need the ability
to build Python C-based modules from source in order to install NumPy and
SciPy. Users on **Unix-based platforms** such as Ubuntu or Mac OS X will need
the traditional C build toolchain installed (e.g. Developer Tools / XCode Tools
on the Mac, or the ``build-essential`` package on Ubuntu or Debian Linux --
basically, anything with ``gcc``, ``make`` and so forth) as well as the Python
development libraries, often named ``python-dev`` or similar:

.. code-block:: console

        # apt-get install build-essential python-dev
        # apt-get build-dep python-scipy

In addition, some plugins require libraries and executables present on the
system to work properly. A good start is install `leptonica
<http://leptonica.com>`_ and `tesseract
<https://code.google.com/p/tesseract-ocr/>`_:

.. code-block:: console

        # apt-get install libtesseract3 tesseract-ocr-eng libleptonica-dev liblept

Further, a `broker
<http://docs.celeryproject.org/en/latest/getting-started/brokers/index.html>`_
is required for `celery <http://celeryproject.org>`_. For testing purposes we
recommend `redis <http://redis.io>`_:

.. code-block:: console

        # apt-get install redis-server

The recommended way to get Nidaba is to **install the latest stable release**
via `pip <https://pip.pypa.io>`_:

.. code-block:: console

        $ pip install nidaba

.. note::
        Deploying python applications can be painful in some circumstances.
        Unfortunately, nidaba is no exception to this and the build process of
        several dependencies is currently of a disastrous quality.
        nidaba should either be installed in disposable virtual machines or if
        installed on a machine that is intended to run other applications, e.g.
        a personal laptop or workstation, we strongly urge you to utilize
        `virtualenv <https://virtualenv.pypa.io>`_.

Alternatively, run pip in the root directory of the `git repository
<https://github.com/openphilology/nidaba>`_:

.. code-block:: console

        $ pip install .

Tests
=====

Per default no dictionaries and OCR models necessary to runs the tests are
installed. To download the necessary files run:

.. code-block:: console

        $ python setup.py download

Afterwards, the test suite can be run:

.. code-block:: console

        $ python setup.py nosetests

Tests for plugins calling external programs, at the time only tesseract and
ocropus, will be skipped if these aren't installed.

Configuration
=============

There are currently two configuration files, one used by the celery framework
and one containing the actual nidaba configuration. Both are written in `YAML
<http://www.yaml.org>`_ so indentation and whitespace is important. They are
installed automatically into ``sys.prefix/etc/nidaba/{celery,nidaba}.yaml``;
usually into the root of the virtualenv containing nidaba or
``/usr/etc/nidaba/``.

The former resembles a `celery configuration object
<http://celery.readthedocs.org/en/latest/configuration.html>`_ and may contain
all available options. The example file looks like this:

.. literalinclude:: ../examples/celery.yaml
        :language: yaml

The later contains essential configuration for several subtasks and the overall
framework:

.. literalinclude:: ../examples/nidaba.yaml
        :language: yaml

storage_path
        The home directory for nidaba to store files created by OCR jobs, i.e.
        the location of the shared storage medium. This may differ on
        different machines in the cluster.

ocropus_models (optional)
        A list of mappings from unique identifiers to storage tupels where a
        tupel is of the format [directory, path] resulting in the absolute path
        storage_path/directory/path. Each mapping defines a single neuronal
        network available to the ocropus OCR task. These have to exist on all
        machines running nidaba and therefore have to be on the common storage medium
        beneath storage_path.

plugin_path (optional)
        A list of additional paths to look for plugins in.

plugins_load (optional)
        An associative array of plugins to load with additional configuration
        data for each plugin. See :doc:`plugins <plugins>` for more information.

Running
=======

Celery requires a worker retrieving tasks from the message broker to actually
execute them.  Starting the celery worker server is quite simple and the only
requirement is that it is NOT run inside the nidaba directory and the message
broker is up and running:

.. code-block:: console

        $ nidaba worker

For further worker options have a look at the `Celery worker documentation
<https://celery.readthedocs.org/en/latest/userguide/workers.html>`_.

Command Line Interface
----------------------

The simplest way to add jobs to the pipeline is using the nidaba command line
utility. It is automatically installed during the installation procedure.

The ``config`` subcommand is used to inspect the current nidabaconfig.py:

.. code-block:: console

        $ nidaba config
        {'lang_dicts': {'german': ['dicts', 'german.dic'],
                        'lojban': ['dicts', 'lojban.dic'],
                        'polytonic_greek': ['dicts', 'greek.dic']},
         'ocropus_models': {'atlantean': ['models', 'atlantean.pyrnn.gz'],
                            'fancy_ligatures': ['models', 'ligatures.pyrnn.gz'],
                            'fraktur': ['models', 'fraktur.pyrnn.gz'],
                            'greek': ['models', 'greek.pyrnn.gz']},
         'plugins_load': {'kraken': {},
                          'leptonica': {},
                          'ocropus': {'legacy': False},
                          'tesseract': {'implementation': 'capi',
                                        'tessdata': '/usr/share/tesseract-ocr'}},
         'storage_path': '~/OCR'}

The ``worker`` subcommand is used to run a celery worker and accepts all
options accepted by the ``celery worker`` command. In fact, running:

.. code-block:: console

        $ nidaba worker

is equivalent to:

.. code-block:: console

        $ celery -A nidaba worker

The ``batch`` subcommand is used to add a job to the pipeline. A rather minimal
invocation looks like this:

.. code-block:: console

        $ nidaba batch --binarize nlbin sauvola --ocr tesseract:eng -- input.png
        90ae699a-7172-44ce-a8bf-5464bccd34d0

It converts the input file ``input.png`` to grayscale, binarizes it using the
Sauvola and nlbin algorithm, and finally runs it through tesseract with the
English language model.

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
        dummy scoring algorithm
--grayscale
        A switch to indicate that input files are already 8bpp grayscale and
        conversion to grayscale is unnecessary.

The ``status`` subcommand is used to retrieve the status of a job. It takes the
return value of a previously executed ``batch`` command. A currently running
command will return PENDING:

.. code-block:: console

        $ nidaba status 90ae699a-7172-44ce-a8bf-5464bccd34d0
        PENDING

When the job has been processed the status command will return a list of paths
containing the final output:

.. code-block:: console

        $ nidaba status 90ae699a-7172-44ce-a8bf-5464bccd34d0
        SUCCESS
        input.png -> /home/mittagessen/OCR/90ae699a-7172-44ce-a8bf-5464bccd34d0/input_img.rgb_to_gray_binarize.nlbin_0.5_0.5_1.0_0.1_80_20_5_90_ocr.tesseract_eng.png.hocr
        input.png -> /home/mittagessen/OCR/90ae699a-7172-44ce-a8bf-5464bccd34d0/input_img.rgb_to_gray_binarize.sauvola_10_0.35_ocr.tesseract_eng.png.hocr

On failure the subtasks that failed and their error message will be printed:

.. code-block:: console

        $ nidaba status 90ae699a-7172-44ce-a8bf-5464bccd34d0
        FAILURE
        ocr.tesseract failed while operating on input_img.rgb_to_gray_binarize.sauvola_10_0.35.png which is based on input.png
        ocr.tesseract failed while operating on input_img.rgb_to_gray_binarize.nlbin_0.5_0.5_1.0_0.1_80_20_5_90.png which is based on input.png

.. include:: ../CONTRIBUTING.rst

.. include:: ../ChangeLog

Licensing and Authorship
========================

This project is licensed under `GPL2.0+
<https://www.gnu.org/licenses/gpl-2.0.html>`_, so feel free to use and adapt as
long as you respect the license. See `LICENSE
<https://github.com/openphilology/nidaba/blob/master/LICENSE>`_ for details.

nidaba is written as part of the `Open Greek and Latin Project
<https://www.dh.uni-leipzig.de/wo/projects/open-greek-and-latin-project/>`_ at
the `Humboldt Chair of Digital Humanities at the University of Leipzig
<https://www.dh.uni-leipzig.de>`_.
