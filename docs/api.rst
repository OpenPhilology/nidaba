.. _api:

=======
Web API
=======

Schema
------

All data is sent and received as JSON.

Root Endpoint
-------------

You can issue a ``GET`` request to the root endpoint to get all the endpoint
categories that the API supports:

Client Errors
-------------

HTTP Verbs
----------

Where possible, the API strives to use appropriate HTTP verbs for each action.

.. autoflask:: nidaba.api:nidaba
   :undoc-static:
   :endpoints:
   :include-empty-docstring:
