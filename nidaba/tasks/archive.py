# -*- coding: utf-8 -*-
"""
nidaba.tasks.archive
~~~~~~~~~~~~~~~~~~~~

Tasks interfacing nidaba output with an external data repository for long-term
archival.
"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba import storage
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@app.task(base=NidabaTask, name=u'nidaba.archival.b2drop')
def archive_metadata(doc, method=u'b2drop'):
    return (doc[0], output_path)

@app.task(base=NidabaTask, name=u'nidaba.archival.b2safe')
def archive_b2safe(doc, method=u'b2safe'):
    return (doc[0], output_path)
