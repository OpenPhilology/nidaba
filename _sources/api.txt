.. _api:

===========
RESTful API
===========

Nidaba includes a RESTful API server and an experimental web user interface. To
start up the server locally just run:

.. code-block:: console

        $ nidaba api_server

To create batches remotely you can use the normal ``nidaba`` commands by adding
the ``-h/--host`` option:

.. code-block:: console

        $ nidaba batch -h http://127.0.0.1:8080/api/v1 --grayscale -l tesseract -o tesseract:languages=eng,extended=True -- input.tif

or:

.. code-block:: console

        $ nidaba status -h http://127.0.0.1:8000/api/v1 cf644c49-01b9-44e3-82fc-a4073f0980ef

Schema
------

All data is sent and received as JSON.

Client Errors
-------------


HTTP Verbs
----------

Where possible, the API strives to use appropriate HTTP verbs for each action.

API Reference
-------------
.. autoflask:: nidaba.api:create_app()
   :undoc-static:
   :endpoints:
   :include-empty-docstring:
