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
- share:  Static, "non binary" files, e.g. images, etc.
- tests: Unit tests.
	- resources: Auxiliary files needed required by the unit tests.

Build
=====

To build Iris run

```
$ pip install .
```

in the root directory. pip is required to extract the dependencies for
setuptools from the requirements file, so there is no reason the run setup.py
directly.

The image deskewing C extension requires the leptonica image processing library:

```
$ apt-get install libleptonica-dev
```

Tests
=====

```
$ setup.py test
```

As mentioned above pip has to be installed.
