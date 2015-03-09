# -*- coding: utf-8 -*-
"""
nibada.tasks.helper
~~~~~~~~~~~~~~~~~

A helper class that all nibada tasks should inherit from to ensure accurate
logging of errors.
"""

from __future__ import absolute_import

from celery import Task
from nibada.celery import app

import json

class NibadaTask(Task):
    """
    An abstract class defining a custom on_failure handler for nibada tasks.
    """
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # XXX: this is race-conditioney and should be replaced with a safe
        # alternative. 
        batch_struct = json.loads(app.backend.get(kwargs['id']))
        batch_struct['errors'].append((args, kwargs, exc.message))
        app.backend.set(kwargs['id'], json.dumps(batch_struct))

