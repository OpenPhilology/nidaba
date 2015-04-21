Overview
========

Nidaba is the central controller for the entire OGL OCR pipeline. It oversees and
automates the process of converting raw images into citable collections of
digitized texts.

It offers the following functionality:

* Grayscale Conversion
* Binarization utilizing
  [Sauvola](http://www.mediateam.oulu.fi/publications/pdf/24.p) adaptive
  thresholding or leptonica's
  [Otsu](http://www.leptonica.com/binarization.html) thresholding with
  background normalization
* Deskewing
* Dewarping
* Integration of [tesseract](http://code.google.com/p/tesseract-ocr/) and
  ocropus OCR engines
* Merging multiple hOCR documents using scoring

As it is designed to use a common storage medium on network attached storage
and the [celery](http://celeryproject.org) distributed task queue it scales
nicely to multi-machine clusters.

Build
=====

To build Nidaba run

```
$ pip install .
```

in the root directory or install using pypi:

```
$ pip install nibada
```

Some useful tasks have external dependencies. A good start is:

```
# apt-get install tesseract-ocr-grc libtesseract3 libleptonica-dev
````

Tests
=====

Per default no dictionaries and OCR models necessary to runs the tests are
installed. To download the necessary files run:

```
$ python setup.py download
```

```
$ python setup.py test
```

Tests for modules that call external programs, at the time only tesseract and
ocropus, will be skipped if these aren't installed.

Running
=======

First edit (the installed) nidaba.yaml and celery.yaml to fit your needs. Have
a look at the [docs](https:///mittagessen.github.io/nidaba) if you haven't set
up a celery-based application before.

Then start up the celery daemon with something like:

```
$ celery -A nidaba worker
```

Next jobs can be added to the pipeline using the nidaba executable:

```
$ nidaba batch --binarize "sauvola:whsize=10;whsize=20;whsize=30;whsize=40,factor=0.6" --ocr tesseract:eng -- ./input.tiff
Preparing filestore....done.             
Building batch...done.
25d79a54-9d4a-4939-acb6-8e168d6dbc7c
```

Using the return code the current state of the job can be retrieved:

```
$ nidaba status 25d79a54-9d4a-4939-acb6-8e168d6dbc7c
PENDING
```

When the job has been processed the status command will return a list of paths
containing the final output:

```
$ nidaba status 25d79a54-9d4a-4939-acb6-8e168d6dbc7c
SUCCESS
input.tiff -> /home/mittagessen/OCR/97150c41-82a9-4935-8063-9295a2eb2a7f/input_img.rgb_to_gray_binarize.sauvola_10_0.35_ocr.tesseract_eng.tiff.hocr
input.tiff -> /home/mittagessen/OCR/97150c41-82a9-4935-8063-9295a2eb2a7f/input_img.rgb_to_gray_binarize.sauvola_20_0.35_ocr.tesseract_eng.tiff.hocr
input.tiff -> /home/mittagessen/OCR/97150c41-82a9-4935-8063-9295a2eb2a7f/input_img.rgb_to_gray_binarize.sauvola_30_0.35_ocr.tesseract_eng.tiff.hocr
input.tiff -> /home/mittagessen/OCR/97150c41-82a9-4935-8063-9295a2eb2a7f/input_img.rgb_to_gray_binarize.sauvola_40_0.6_ocr.tesseract_eng.tiff.hocr
```


Documentation
=============

Want to learn more? [Read the Docs](https:///openphilology.github.io/nidaba/)
