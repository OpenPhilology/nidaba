# -*- coding: utf-8 -*-
"""
nidaba.tasks.helper
~~~~~~~~~~~~~~~~~~~

A helper class that all nidaba tasks should inherit from to ensure accurate
logging of errors.
"""

from __future__ import absolute_import

from celery import Task
from inspect import getcallargs, getargspec
from nidaba.celery import app

import json

class NidabaTask(Task):

    """
    An abstract class propagating unused function arguments through the
    execution chain. This means that no task should accept arbitrary (**kwargs)
    arguments as they won't be forwarded to the actual function and will be
    retained through the whole chain.
    """
    abstract = True
    acks_late = True

    def __call__(self, *args, **kwargs):
        # if args is a dictionary we merge it into kwargs
        if len(args) == 1 and isinstance(args[0], dict):
            kwargs.update(args[0])
            args = ()
        # and then filter all tracking objects (root document, job id, ...) out
        # again 
        fspec = getargspec(self.run)
        nkwargs = {}
        tracking_kwargs = {}
        while kwargs:
            k, v = kwargs.popitem()
            if k in fspec.args:
                nkwargs[k] = v
            else:
                tracking_kwargs[k] = v
        try:
            ret = super(NidabaTask, self).__call__(*args, **nkwargs)
        except Exception as e:
            # write error to backend and reraise exception
            batch_struct = json.loads(app.backend.get(tracking_kwargs['id']))
            batch_struct['errors'].append((nkwargs, tracking_kwargs, e.message))
            app.backend.set(tracking_kwargs['id'], json.dumps(batch_struct))
            raise
        tracking_kwargs['doc'] = ret
        return tracking_kwargs
