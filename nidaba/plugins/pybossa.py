# -*- coding: utf-8 -*-
"""
nidaba.plugins.pybossa
~~~~~~~~~~~~~~~~~~~~~~
"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba import storage
from nidaba.celery import app
from nidaba.nidabaexceptions import NidabaPluginException
from nidaba.tasks.helper import NidabaTask

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def setup(*args, **kwargs):
    try:
        global pbclient
        import pbclient
        pbclient.set('endpoint', kwargs.get('server'))
        pbclient.set('api_key', kwargs.get('api_key'))
        global project
        project = pbclient.find_project(short_name=kwargs.get('project'))[0].data['id']
    except Exception as e:
        raise NidabaPluginException(e.message)


@app.task(base=NidabaTask, name=u'nidaba.archive.pybossa')
def archive_pybossa(doc, method=u'archive_pybossa'):
    """
    Adds recognition result to a pybossa service for postcorrection.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files.

    Returns:
        The input storage tuple.
    """
    logger.debug('Creating pybossa task {} {}'.format(*doc))
    for d in doc:
        pbclient.create_task(project, {'batch_id': doc[0], 'xml': storage.get_url(*d)})
    return doc
