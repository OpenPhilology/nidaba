:title: Configuring the Iris pipeline
:description: Learn how to configure Iris

.. _configuring_iris:

Configuring the Iris Pipeline
=============================

There are currently two configuration files, one used by the celery framework
and one containing the actual Iris configuration. Both are written in `YAML
<http://www.yaml.org>`_ so indentation and whitespace is important. They are
installed automatically into sys.prefix/etc/iris/{celery,iris}.yaml; usually
into the root of the virtualenv containing iris or /usr/etc/iris/.

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
        The home directory for Iris to store files created by OCR jobs, i.e.
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
	machines running iris and therefore have to be on the common storage medium
	beneath storage_path.
