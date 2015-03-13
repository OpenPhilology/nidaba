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

The image processing C extension requires the leptonica image processing
library (>=1.70, available from Debian Jessie):

```
$ apt-get install libleptonica-dev
```

Per default no dictionaries and OCR models (including data necessary to run
some tests) are installed. To download the necessary files run:

```
$ python setup.py download
```

Tests
=====

```
$ python setup.py test
```

Tests for modules that call external programs, at the time only tesseract and
ocropus, will be skipped if these aren't installed.

Running
=======

First edit (the installed) nidaba.yaml and celery.yaml to fit your needs. Have
a look at the [docs](https:///nidaba.rtfd.org/) if you haven't set up a
celery-based application before.

Then start up the celery daemon with something like:

```
$ celery -A nidaba worker
```

Next jobs can be added to the pipeline using the nidaba executable:

```
$ nidaba batch --binarize "sauvola:whsize=10;whsize=20;whsize=30;whsize=40,factor=0.6" --ocr tesseract:eng -- ./input.tiff
35be45e9-9d6d-47c7-8942-2717f00f84cb
```

Using the return code the current state of the job can be retrieved:

```
$ nidaba status 35be45e9-9d6d-47c7-8942-2717f00f84cb
PENDING
```

When the job has been processed the status command will return a list of paths
containing the final output:

```
$ nidaba status 35be45e9-9d6d-47c7-8942-2717f00f84cb
SUCCESS
        /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_10_0.3_ocr_tesseract_eng.tiff.hocr
        /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_20_0.3_ocr_tesseract_eng.tiff.hocr
        /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_30_0.3_ocr_tesseract_eng.tiff.hocr
        /home/mittagessen/OCR/01c00777-ea8e-46e1-bc68-95023c7d29a1/input_rgb_to_gray_binarize_sauvola_40_0.3_ocr_tesseract_eng.tiff.hocr
```


Documentation
=============

Want to learn more? [Read the Docs](https:///nidaba.readthedocs.org/)

