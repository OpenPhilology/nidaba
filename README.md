Overview
========

Iris is the central controller for the entire OGL OCR pipeline. It oversees and
automates the process of converting raw images into citable collections of
digitized texts. Images can be uploaded directly via Iris' RESTful web portal,
or can be selected from preexisting images located on Iris' image repository.

Project Structure
=================

- docs: Miscellaneous documentation other than the README.
- iris: The Iris python package
	- web: Contains all code for communicating with the frontend pages, flask routing, etc.
- exts: C extensions
- resources: Static, "non binary" files, e.g. ocropus models, dictionaries etc.
- tests: Unit tests.
	- resources: Auxiliary files required by the unit tests.

Installation
============

First edit iris/celeryconfig.py and iris/irisconfig.py to fit your needs.
Running a distributed cluster requires a shared storage medium (e.g. NFS) on
all nodes.

To build Iris run

```
$ pip install .
```

in the root directory. pip is required to extract the dependencies for
setuptools from the requirements file, so there is no reason the run setup.py
directly.

The image processing C extension requires the leptonica image processing
library (>=1.70, available from Debian Jessie):

```
$ apt-get install libleptonica-dev
```

Per default no dictionaries and OCR models (including data necessary to run
tests) are installed. To download the necessary files run:

```
$ python setup.py download
```


Tests
=====

```
$ python setup.py test
```

As mentioned above pip and the models have to be installed.

Running the tests requires a working tesseract with ancient greek language
files. 

Running
=======

Then start up the celery daemon with something like:

```
$ celery -A iris.tasks worker
```

Next jobs can be added to the pipeline using the iris executable:

```
$ iris batch --binarize sauvola:10,20,30,40 --ocr tesseract:eng -- ./input.tiff
35be45e9-9d6d-47c7-8942-2717f00f84cb
```

Using the return code the current state of the job can be retrieved:

```
$ iris status 35be45e9-9d6d-47c7-8942-2717f00f84cb
PENDING
```

When the job has been processed the status command will return a list of paths
containing the final output:

```
$ iris status 35be45e9-9d6d-47c7-8942-2717f00f84cb
SUCCESS
        /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_10_0.3_ocr_tesseract_eng.tiff.hocr
        /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_20_0.3_ocr_tesseract_eng.tiff.hocr
        /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_30_0.3_ocr_tesseract_eng.tiff.hocr
        /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_40_0.3_ocr_tesseract_eng.tiff.hocr
```

Recommendations
===============

There are no sane default thresholds for the binarization algorithms as correct
values are highly dependent on the nature and quality of the input documents.
Some sensible values as used by Bruce Robertsons rigaudon for Otsu's
thresholding ({'method': 'binarize', 'algorithm': 'otsu'}) are:

```
94,97,100,103,105,107,109,112,115,117
```

Ocropus' binarization parameters using Sauvola are:

```
{'method': 'binarize', 'thresh': 40, 'factor': 0.3}
```


Issues
======

[1]:https://github.com/travis-ci/travis-ci/issues/1778

* Unparametrized function are run several times, for example rgb_to_gray will
  be run for all chains even though the output will be identical on each run.
