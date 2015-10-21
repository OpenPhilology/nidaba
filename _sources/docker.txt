Docker Container
================

A docker image containing a working nidaba installation with the leptonica,
tesseract, and kraken plugins preconfigured is available from the `Docker Hub
<https://hub.docker.com/r/openphilology/nidaba/>`_. If you haven't used docker
before there is an excellent introduction at their `website
<http://docs.docker.com/linux/started/>`_.

Download
--------

To download the latest image (~4Gb) from docker hub run:

.. code-block:: console

        $ docker pull openphilology/nidaba

If everything went right it is then possible to enter the container through:

.. code-block:: console

        $ docker run -it openphilology/nidaba

A short help message will be displayed including a warning that all work is
ephemeral by default.

Directory Sharing
-----------------



Persistence
-----------


