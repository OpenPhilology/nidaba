# -*- coding: utf-8 -*-
"""
nidaba.tasks.helper
~~~~~~~~~~~~~~~~~~~

A helper class that all nidaba tasks should inherit from to ensure accurate
logging of errors.
"""

from __future__ import absolute_import

from celery import Task
from nidaba.celery import app

import json


class NidabaTask(Task):

    """
    An abstract class defining a custom on_failure handler for nidaba tasks.
    """
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # XXX: this is race-conditioney and should be replaced with a safe
        # alternative.
        batch_struct = json.loads(app.backend.get(kwargs['id']))
        batch_struct['errors'].append((args, kwargs, exc.message))
        app.backend.set(kwargs['id'], json.dumps(batch_struct))
