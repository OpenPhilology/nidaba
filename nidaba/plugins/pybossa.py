# -*- coding: utf-8 -*-
"""
nidaba.plugins.pybossa
~~~~~~~~~~~~~~~~~~~~~~

Adds an pybossa interface.

Run:

    $ pip install pybossa-client

and set server, apikey, and project in the configuration file.
"""

from __future__ import unicode_literals, print_function, absolute_import

import os
import shutil
import regex
import requests

from nidaba import api
from nidaba import storage
from flask_restful import url_for

logger = get_task_logger(__name__)


def setup(*args, **kwargs):
    global pbclient
    import pbclient
    pbclient.set('endpoint', kwargs.get(u'server'))
    pbclient.set('api_key', kwargs.get(u'apikey'))
    global pybossa_project
    pybossa_project = pbclient.find_project(short_name=kwargs.get(u'project'))[0]
    global pybossa_app
    # XXX: request independent URL generation requires an explicit server name.
    # Ideally we'd get it from somewhere else.
    global pybossa_app
    pybossa_app = api.create_app()
    pybossa_app.config['SERVER_NAME'] = kwargs.get(u'nidaba_server')


@app.task(base=NidabaTask, name=u'nidaba.archive.pybossa')
def archive_pybossa(doc, method=u'pybossa'):
    """
    "Archives" the output by creating tasks on a remote pybossa instance.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string append to all output files

    Returns:
        The input storage tuple
    """

    input_path = storage.get_abs_path(*doc)
    with pybossa_app.app_context():
        logger.debug('Creating task {} {} on pybossa'.format(*doc))
        pbclient.create_task(pybossa_project, {
                             'batch_id': doc[0],
                             'xml': url_for('api.page', batch=doc[0], file=doc[1])
                            })
    return doc
