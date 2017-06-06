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
from nidaba import tei

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def setup(*args, **kwargs):
    try:
        global pbclient
        import pbclient
        pbclient.set('endpoint', kwargs.get('server'))
        pbclient.set('api_key', kwargs.get('api_key'))
    except Exception as e:
        raise NidabaPluginException(e.message)


@app.task(base=NidabaTask, name=u'nidaba.archive.pybossa',
          arg_values={'name': 'str', 'description': 'str'})
def archive_pybossa(doc, method=u'archive_pybossa', name='', description=''):
    """
    Adds recognition result to a pybossa service for postcorrection.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files.

    Returns:
        The input storage tuple.
    """
    logger.debug('Creating pybossa project named {}'.format(name))
    proj = pbclient.create_project('{} ({})'.format(name, doc[0][0]), doc[0][0], description)
    logger.debug('Creating pybossa tasks for docs {}'.format(doc))
    for d in doc:
        data = tei.OCRRecord()
        with storage.StorageFile(*d, mode='rb') as fp:
            data.load_tei(fp)
            for line_id, line in data.lines.iteritems():
                text = u''
                for seg in line['content'].itervalues():
                    text += u''.join(x['grapheme'] for x in seg['content'].itervalues())
                pbclient.create_task(proj.id, {
                    'image': data.img,
                    'dimensions': data.dimensions,
                    'line_text': text.encode('utf-8'),
                    'bbox': [
                        line['bbox'][0],
                        line['bbox'][1],
                        line['bbox'][2],
                        line['bbox'][3]
                    ]
                })
    return doc
