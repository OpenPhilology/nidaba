:title: Preparing Celery
:description: Preparatory steps to let Iris accept jobs

.. _preparing_celery:

Running the celery worker server
================================

Starting the celery worker server is quite simple and the only requirement is
that it is NOT run inside the iris directory and the message broker is up and
running:

.. code-block:: console

	$ celery -A iris.tasks worker

For further worker server options have a look at `celery`.

.. _`celery`: https://celery.readthedocs.org/en/latest/
