:title: Concepts
:description: Deis combines a variety of common preprocessing and OCRing steps into a single job.

.. _concepts:

Concepts
========

Iris is a lightweight and flexible platform that aims to combine all steps from
scanned input pages to the best possible text.

.. _concepts_tasks:

Tasks
-----

Each atomic function of iris is a single task. On the most basic level iris is
nothing more than a collection of tasks that can be combined in a multitude of
ways to alter input documents.

A task can be everything from an abstract process, e.g. binarization, to a
specific invocation of a particular program, e.g. the ocr_tesseract task. Some
tasks are native python code while others call external software.

.. _concepts_celery:

Celery
------

Executing singular tasks is rather useless and celery is used to coordinate and
distribute the execution of a set of tasks, commonly called a job. A job is
nothing more than the execution of tasks in a predefined order and
parallelization level. 

Celery uses a message broker to communicate the tasks to be run to the machines
of the compute cluster. To learn more about celery peruse its
[documentation](https://celery.readthedocs.org/en/latest/).

.. _concepts_storage:

Storage
-------

While celery can be used to distribute tasks it is unsuitable for file
distribution. To ensure that each machine has access to the same data a common
storage medium has to be used. Iris utilizes a simple directory on the file
system for all its storage purposes which can be placed on a network file
system like NFS to realize the synchronization between all machines in the
cluster.

For single machine use a normal directory set apart from all other use is
sufficient.

All tasks of a job usually operate inside a single subdirectory on the shared
medium. This directory should be globally unique and ensures that there are no
conflicts between jobs.

See Also
--------
* :ref:`Using Iris <using_iris>`
* :ref:`Troubleshooting Iris <troubleshooting_iris>`
