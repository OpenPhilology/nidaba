Overview
========

Iris is the central controller for the entire OGL OCR pipeline. It oversees and
automates the process of converting raw images into citable collections of
digitized texts. Images can be uploaded directly via Iris' RESTful web portal,
or can be selected from preexisting images located on Iris' image repository.

It offers the following functionality:

* Grayscale Conversion
* Binarization utilizing
  [Sauvola](http://www.mediateam.oulu.fi/publications/pdf/24.p) adaptive
  thresholding or leptonica's
  [Otsu](http://www.leptonica.com/binarization.html) thresholding with
  background normalization
* Deskewing
* Dewarping
* Integration of [tesseract](http://code.google.com/p/tesseract-ocr/) and ocropus OCR
  engines
* Merging multiple hOCR documents using scoring

As it is designed to use a common storage medium on network attached storage
and the [celery](http://celeryproject.org) distributed task queue it scales
nicely to multi-machine clusters.

Build
=====

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
files and an installed ocropus suite.

Running
=======

First edit (the installed) iris.yaml and celery.yaml to fit your needs. Have a
look at the [docs](https:///ogl-iris.rtfd.org/) if you haven't set up a
celery-based application before.

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


Documentation
=============

Want to learn more? [Read the Docs](https:///ogl-iris.readthedocs.org/)

