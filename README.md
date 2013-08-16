1. Overview
Iris is the central controller for the entire OGL OCR pipeline. It oversees and automates the process of converting raw images into citable collections of digitized texts. Images can be uploaded directly via Iris' RESTful web portal, or can be selected from preexisting images located on Iris' image repository. All images and texts processed by Iris are uniquely identifiable and retrievable through automatically generated URNs which Iris automatically assigns to everything it processes. In addition, all texts produced by Iris can be edited or revised concurrently by an arbitrary number of users without data loss. For more information on Iris' implementation, see docs/schematic.png


2. Repo Contents
	docs: Miscellaneous documentation other than the README and requirements files.
	iris: The Iris python package
		static:  Static, "non binary" files, e.g. images, etc.
		DAO (Database Access Object): Contains all code for communicating with the persistent/DB layer. This will include code for communicating with the wrapped GIT API for text version control, the OCR-image DB, etc. No part of Iris implements any kind of persistent storage except through a DAO module.
		test: Unit tests (duh).
		web: Contains all code for communicating with the frontend pages, handling REST, etc.	OCR: Contains all code for communicating with the OCR engine, possibly distributing/parallelizing OCR tasks. Neither this, nor an part of Iris contains actual OCR algorithms.

