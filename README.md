Overview
========

Iris is the central controller for the entire OGL OCR pipeline. It oversees and
automates the process of converting raw images into citable collections of
digitized texts. Images can be uploaded directly via Iris' RESTful web portal,
or can be selected from preexisting images located on Iris' image repository.
All images and texts processed by Iris are uniquely identifiable and
retrievable through automatically generated URNs which Iris automatically
assigns to everything it processes. In addition, all texts produced by Iris can
be edited or revised concurrently by an arbitrary number of users without data
loss. For more information on Iris' implementation, see docs/schematic.png


Project Structure
=================

- docs: Miscellaneous documentation other than the README.
- iris: The Iris python package
	- web: Contains all code for communicating with the frontend pages, flask routing, etc.
- exts: C extensions
- share: Static, "non binary" files, e.g. images, etc.
- tests: Unit tests.
	- resources: Auxiliary files required by the unit tests.

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

If a manual install is required, don't forget to install the apropriate image
format libraries and their headers (libtiff, libpng, libjpeg) or run:

```
$ apt-get build-dep leptonlib
```

If you are building leptonica from source at a nonstandard prefix, be sure
to pass the following arguments to build_ext: -R &lt;prefix&gt;/lib -I &lt;prefix&gt;/include -L &lt;prefix&gt;/lib

Tests
=====

```
$ setup.py test
```

As mentioned above pip has to be installed.

Running the tests requires a working tesseract with ancient greek language
files. 

Note that users of Python 2.7.3 (The version in Debian Wheezy) will see
[this][1] error after a successful run of setup.py test.
This is a bug in Python 2.7.3 and is patched in later versions.

Running
=======

First edit celeryconfig.py and irisconfig.py to fit your needs. Running a
distributed cluster requires a shared storage medium (e.g. NFS) on all nodes.
Then start up the celery daemon with something like:

```
$ celery -A iris.tasks worker
```

Right now there isn't an easy to use script available. Core functionality is
exposed by the ''batch'' function of the iris package:

```
>>> import iris
>>> iris.iris.batch({'batch_id': u'1234', 'input_files': [u'input.tiff'], 'actions': 
[
	[
		[{'method': 'rgb_to_gray'}], 
		[{'method':'binarize', 'thresh': 10}, {'method': 'binarize', 'thresh': 5}], 
		[{'method': 'ocr_tesseract', 'languages': ['eng']}]
	],
	[
		[{'method': 'blend_hocr'}]
	]
]})
'6222f675-330e-461c-94de-1d0ea0a2f444'
```

For the less telepathically inclined: batch_id is a unique descriptor
identifying the batch, input_files are obviously the input data, situated in
the storage backend under the batch_id, and actions are the transformations
applied to the input data. Those are a list of lists of lists where the
innermost lists are methods running in parallel, while middle and outermost
list(s) are run sequentially. So the above example is converted to 2 execution
chains the run in parallel

```
rgb_to_gray -> binarize (thresh: 10) -> ocr_tesseract
rgb_to_gray -> binarize (thresh: 5) -> ocr_tesseract
```

After these are finished (next outer list) new execution chains will be created
from the next list (in this case just one):

```
merge_hocr
```
The final result will be the return value(s) of the last method(s) of the last
chain(s).

Progress of the batch can be checked using the return value of the batch function:

```
>>> iris.get_progress('6222f675-330e-461c-94de-1d0ea0a2f444')
(2, 4)
```

The final output can be gathered using the get_results function:

```
>>> iris.get_results('6222f675-330e-461c-94de-1d0ea0a2f444')
[['1234', 'foo.txt'],['1234', 'bar.txt'] ...]
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
