Iris Developer Guide
====================

Overview
--------

Iris is designed according to the following principles:

1. Iris is written in one language: Python, v2.7+. While there are a VERY limited number of dependencies (most notably Gamera and Redis) which exist in other languages, Iris' source is Python. This is to remedy the many problems which arose out of the previous system core being a combination of java, python and bash.
2. Rigid standards and requirements for testing, version control, etc. 
3. A unified system for versioning/dependency management.
4. A platform independent interface.

General Coding Standards and Guidelines for Iris
------------------------------------------------

1. PEP8 compliance. See http://www.python.org/dev/peps/pep-0008/
2. Indentation is 4 spaces, NOT a tab. Do not use tabs for indentation.
3. Proper logging. However, the Iris logging standards are still under development. Until then, refer to the standard python logging library at http://docs.python.org/2/library/logging.html
4. Commenting!! Code must be properly commented. See the commenting section below and PEP8 for details.
5. Proper handling of encodings. All python source files should use UTF-8.
6. Iris uses Python's "new style" objects. This means that all classes must explicitly inherit "object".

Commenting requirements are as follows:

1. A docstring comment for every module, class, and function, describing its purpose and functionality.
2. "Exotic code" should have a short line comment explaining its purpose. Obviously code should be as self-describing as possible, but in other cases, comments must be used.
3. No useless comments. For example, do not write: x = x + 1 # Incrementing x.

Version Control Procedures
--------------------------

Iris' source is managed with Git. It's repository can be found at: https://github.com/OpenPhilology/Iris

Contributors to Iris must upload source according to the following procedure:

1. Initial fork/Upstream pull
2. Implemenation of features/changes
3. Ensure all unit tests pass.
4. Upstream pull. If the upstream changes have broken tests or radically change your changes, return to step 2 until tests are passing again.
5. Submit pull request. If the pull request is accpeted, congratulations! If you want to implement another change, make sure to start at step 1 with fresh upstream pull! Otherwise go back to step 2.

If you encounter any difficulty working with Git or just need to brush up, refer to Atlassian's Git tutorials at: https://www.atlassian.com/git/tutorial which are excellent.


Pull requestes will be automatically reject for any of the following reasons:

1. Lack of tests/failing tests.
2. Lack of proper commenting.
3. Inappropriate hardcoding.
4. Introduction of a redundant dependency, an inferior dependency, or an older version of an existing dependency.
5. Misplaced code (i.e. code not in the proper place within the project hiararchy.)
6. "Smelly" or mathematically substandard code. (i.e. implementing a factorial function with recursion instead of iteration.)
7. Lack of proper logging/exception handling.
8. Failure to handle encodings properly.


Versioning and Dependency Management
------------------------------------

Versioning:
Iris maintains two kinds of principal branches. These are the main development branch, and LTS (long term support) branches. The dev branchs are the master branch and new feature development branches. These are kept up to date with the latest dependencies.
The LTS branches are stable versions which are available with bundled copies of all their dependencies. This is to ensure usable distributios of Iris exist in the event that new dependency updates cause temporary instability in the dev branches at the same time an older dependency version becomes unavailable. LTS branches are maintained just like the dev branch, but with critical dependency updates only.

Dependencies:
Iris uses pip and Pypi for all its dependency management. Whenever a new commit us uploaded to a branch, a copy of the pip generated requirements file is included with that commit. This way, all dependencies can be automatically synchronized with Iris source at any point in the version history using pip freeze and pip install -r.
If you are adding a feature which may require a new dependency, you MUST state it in the pull request message.

There are currently two exceptions to this rule: redis and gamera, as these are not included in Pypi. Currently, they are to be kept up do date manually, with incompatiblities treated as any other bug.

Final note: Please know that commits prior to October 29 2013 were primarily for experimentation with different libraries and basic preliminary work. Code from them should be considered unreliable/uncompliant with the above standards, and should NOT be taken as standards.

If you have any questions or would like to contribute, please contact to openPhilology@informatik.uni-leipzig.de.
