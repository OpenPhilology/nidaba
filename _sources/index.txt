======
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
        Option Groups <options>
        TEI <tei>
        Web API <api>
        API Docs <source/modules>

Nidaba does a bunch of things for you:

- `Grayscale Conversion <http://pillow.readthedocs.org/en/latest/reference/Image.html#PIL.Image.Image.convert>`_
- `Binarization <http://en.wikipedia.org/wiki/Thresholding_%28image_processing%29>`_
- `Deskewing <http://www.leptonica.com/skew-measurement.html>`_
- `Dewarping <http://www.leptonica.com/dewarping.html>`_
- `OCR <http://en.wikipedia.org/wiki/Optical_character_recognition>`_
- :ref:`Spell-checking <spell-checking>`
- :ref:`TEI output <tei_output>`
- :ref:`Format Conversion <output_layer>` 


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

To also install the prerequisites for the :py:mod:`nidaba.plugins.kraken`
plugin it is possible to install the `kraken
<http://mittagessen.github.io/kraken>`_ bundle instead:

.. code-block:: console
        
        $ pip install nidaba[kraken]

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

.. code-block:: yaml

        BROKER_URL: 'redis://127.0.0.1:6379'
        CELERY_RESULT_BACKEND: 'redis://127.0.0.1:6379'
        CELERY_TASK_SERIALIZER: 'json'
        CELERY_RESULT_SERIALIZER: 'json'
        CELERY_ACCEPT_CONTENT: ['json']

The later contains essential configuration for several subtasks and the overall
framework:

.. code-block:: yaml

        storage_path: ~/OCR
        redis_url: 'redis://127.0.0.1:6379'
        lang_dicts:
          polytonic_greek: {dictionary: [dicts, greek.dic], 
                            deletion_dictionary: [dicts, del_greek.dic]}
          latin: {dictionary: [dicts, latin.dic], 
                            deletion_dictionary: [dicts, del_latin.dic]}
        ocropus_models:
          greek: [models, greek.pyrnn.gz]
          atlantean: [models, atlantean.pyrnn.gz]
          fraktur: [models, fraktur.pyrnn.gz]
          fancy_ligatures: [models, ligatures.pyrnn.gz]
        kraken_models:
          default: [models, en-default.pronn]
          fraktur_clstm: [models, fraktur.clstm]
        plugins_load:
          tesseract: {implementation: capi,
                     tessdata: /usr/share/tesseract-ocr}
          ocropus: {}
          kraken: {}
          leptonica: {}


``storage_path``

The home directory for nidaba to store files created by OCR jobs, i.e. the
location of the shared storage medium. This may differ on different machines in
the cluster.

``redis_url``

URL to the Redis key-value store which is required in addition to celery's
broker but may be shared.

``lang_dicts`` (optional)

See the :ref:`spell-checking <spell-checking>` documentation for further
information.

``ocropus_models`` and ``kraken_models`` (optional)

See the :doc:`plugins <plugins>` documentation for further information.

``plugins_load`` (optional)

An associative array of plugins to load with additional configuration data for
each plugin. See :doc:`plugins <plugins>` for more information.

Running
=======

Celery requires a worker retrieving tasks from the message broker to actually
execute them. Starting the celery worker server is quite simple and the only
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

Configuration and Plugins
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``config`` subcommand is used to inspect the current nidabaconfig.py:

.. code-block:: console

        $ nidaba config
        {'kraken_models': {'goodell': ['models', 'goodell.pyrnn.pronn'],
                           'loeb_2013': ['models', 'loeb.pronn'],
                           'migne': ['models', 'migne.pronn'],
                           'migne_2013': ['models', 'migne_2013.pronn'],
                           'non-teubner': ['models', 'non-teubner-german-serif.pronn'],
                           'omnibus': ['models', 'omnibus.pyrnn.pronn'],
                           'porson': ['models', 'porson.pyrnn.pronn'],
                           'rahlfs': ['models', 'rahlfs.pyrnn.pronn'],
                           'teubner': ['models', 'teubner-serif.pyrnn.pronn']},
         'lang_dicts': {'latin': {'deletion_dictionary': ['dicts', 'del_latin.dic'],
                                  'dictionary': ['dicts', 'latin.dic']},
                        'polytonic_greek': {'deletion_dictionary': ['dicts',
                                                                    'del_greek.dic'],
                                            'dictionary': ['dicts', 'greek.dic']}},
         'ocropus_models': {'atlantean': ['models', 'atlantean.pyrnn.gz'],
                            'fancy_ligatures': ['models', 'ligatures.pyrnn.gz'],
                            'fraktur': ['models', 'fraktur.pyrnn.gz'],
                            'greek': ['models', 'greek.pyrnn.gz']},
         'plugins_load': {'kraken': {},
                          'tesseract': {'implementation': 'capi',
                                        'tessdata': '/home/mittagessen/git'}},
         'redis_url': 'redis://127.0.0.1:6379',
         'storage_path': '~/OCR'}

To see which plugins are available and enabled the ``plugins`` subcommand may be used:

.. code-block:: console

        $ nidaba plugins
        ocropus (disabled)
        tesseract (enabled)
        kraken (disabled)
        leptonica (disabled)

Workers
~~~~~~~

The ``worker`` subcommand is a shorthand to start up a celery worker. In fact

.. code-block:: console

        $ nidaba worker

is equivalent to:

.. code-block:: console

        $ celery -A nidaba worker

except that the latter will accept additional command line parameters.

Batches
~~~~~~~

The ``batch`` subcommand is used to add a job to the pipeline. A rather minimal
invocation looks like this:

.. code-block:: console

        $ nidaba batch -b sauvola:whsize=10,factor=0.35 -l tesseract -o tesseract:languages=\[grc,eng\],extended=True -- 0007.tif
        90ae699a-7172-44ce-a8bf-5464bccd34d0

It converts the input file ``input.png`` to grayscale, binarizes it using the
Sauvola algorithm, creates a page segmentation of the image using tesseract's
algorithm, and finally runs everything through tesseract with the English and
Greek language models, creating a TEI XML file.

There are several groups of options, each associated with a particular set of
functions of the pipeline. An option may appear multiple times to define
additional execution paths similar to adding new branches to the leaves of a
tree where each leaf is one result of the, logically, preceding group of
options. All paths through this tree will then be executed by the workers in
the cluster.

Each option must follow the same format
``algorithm:param1=val1,param2=\[val2,val3\],...,paramN=N`` where parameters
are divided by ``,`` and lists of parameter values are contained in
``\[val1,val2\]`` statements. Additionally, there is a helper preamble
``file:`` which must be followed by a valid path to a file. This file will be
copied to the common storage medium and its new location will be used instead
of the path when executing the function.

Available option groups in order of processing are:

--binarize / -b
        Defines binarization parameters. See the :ref:`binarization
        <bin>` documentation for more details.

--segmentation / -l
        Defines page segmentation parameters. See the :ref:`segmentation
        <segmentation_heading>` documentation for more details.

--ocr / -o 
        Defines OCR parameters. See the :ref:`OCR <ocr_heading>` documentation
        for more details.

--postprocessing / -p
        Defines parameters of various postprocessing methods. See the
        :ref:`spell-checking <spell-checking>` documentation for more details.

--stats / -s
        Defines parameters of metrics. See the :ref:`metrics` documentation for
        more details.

There is one additional option which is technically part of another option
group but can't be included in other groups for several reasons:

\-\-grayscale
        A switch to indicate that input files are already 8bpp grayscale and
        conversion to grayscale is unnecessary.

Batch status
~~~~~~~~~~~~

The ``status`` subcommand is used to retrieve the status of a job. It takes the
return value of a previously executed ``batch`` command. A currently running
command will return pending and some additional information about the batch:

.. code-block:: console

        $ nidaba status 90ae699a-7172-44ce-a8bf-5464bccd34d0
        Status: pending 
        
        4/4 tasks completed. 0 running.
        
        Output files:

When the job has been processed the status command will return a list of paths
containing the final output:

.. code-block:: console

        $ nidaba status 90ae699a-7172-44ce-a8bf-5464bccd34d0
        Status: success (final)
        
        4/4 tasks completed. 0 running.
        
        Output files:
        
        0007.tif → 0007_ocr.tesseract_eng_grc.tif.xml
        0009.tif → 0009_ocr.tesseract_eng_grc.tif.xml

On failure the subtasks that failed and their error message will be printed:

.. code-block:: console

        $ nidaba status 90ae699a-7172-44ce-a8bf-5464bccd34d0
        Status: failed (final)
        
        1/2 tasks completed. 0 running.
        
        Output files:
        
        Errors:
        
        nidaba.ocr.kraken (0007.tif): IOError: [Errno 2] No such file or directory: '/home/mittagessen/OCR/t/e/u/b/n/e/r/-/s/e/r/i/f/-/2/0/1/3/-/1/2/-/1/6/-/1/1/-/2/6/-/0/0/0/6/7/0/0/0/p/y/r/n/n/p/r/o/n/n'

A batch may contain failed and running tasks at the same time. To be able to
distinguish failed batches which are still running and finalized failed batches
the status command will add the ``(final)`` indicator on the latter.

It is also possible to increase the verbosity of the error output:

.. code-block:: console

        $ nidaba status -vv 90ae699a-7172-44ce-a8bf-5464bccd34d0
        Status: failed (final)

        288/384 tasks completed. 0 running.

        Output files:

        Errors:
        
        nidaba.ocr.kraken (0046.tif, {u'model': u'teubner'}):   File "/home/mittagessen/git/nidaba/nidaba/tasks/helper.py", line 91, in __call__
            ret = super(NidabaTask, self).__call__(*args, **nkwargs)
          File "/home/mittagessen/envs/nidaba/local/lib/python2.7/site-packages/celery/app/trace.py", line 438, in __protected_call__
            return self.run(*args, **kwargs)
          File "/home/mittagessen/git/nidaba/nidaba/plugins/kraken.py", line 152, in ocr_kraken
            rnn = models.load_any(model)
          File "/home/mittagessen/git/kraken/kraken/lib/models.py", line 110, in load_any
            seq = load_pyrnn(fname)
          File "/home/mittagessen/git/kraken/kraken/lib/models.py", line 211, in load_pyrnn
            with io.BufferedReader(of(fname, 'rb')) as fp:
        IOError: [Errno 2] No such file or directory: '/home/mittagessen/OCR/t/e/u/b/n/e/r/-/s/e/r/i/f/-/2/0/1/3/-/1/2/-/1/6/-/1/1/-/2/6/-/0/0/0/6/7/0/0/0/p/y/r/n/n/p/r/o/n/n'
        

.. _contributing:

Contributing
============

Every open source project lives from the generous help by contributors
that sacrifice their time and nibada is no different.

Here are a few hints and rules to get you started:

-  No contribution is too small; please submit as many fixes for typos
   and grammar bloopers as you can!
-  Don’t *ever* break backward compatibility.
-  *Always* add tests and docs for your code.
-  This is a hard rule; patches with missing documentation
   won’t be merged. If a feature is not documented, it doesn’t
   exist.
-  Obey `PEP8 <http://www.python.org/dev/peps/pep-0008/>`__ and
   `PEP257 <http://www.python.org/dev/peps/pep-0257/>`__.
-  Write good commit messages.
-  Ideally,
   `squash <http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html>`__
   your commits, i.e. make your pull requests just one commit.
-  If you're not comfortable with using git, please use git format-patch
   and send me the resulting diff.

If you have something great but aren’t sure whether it adheres -- or
even can adhere -- to the rules above: **please submit a pull request
anyway**!

In the best case, we can mold it into something, in the worst case the
pull request gets politely closed. There’s absolutely nothing to fear.

Thank you for considering to contribute to nibada! If you have any
question or concerns, feel free to reach out to us.


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
