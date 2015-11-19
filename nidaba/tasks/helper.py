# -*- coding: utf-8 -*-
"""
nidaba.tasks.helper
~~~~~~~~~~~~~~~~~~~

A helper class that all nidaba tasks should inherit from to ensure accurate
logging of errors.
"""

from __future__ import unicode_literals, print_function, absolute_import

from celery import Task
from inspect import getargspec
from redis import WatchError
from nidaba.config import Redis
from celery.utils.log import get_task_logger

import json
import traceback
import sys

logger = get_task_logger(__name__)

def _redis_set_atomically(batch_id, subtask, key, val):
    """
    Atomically sets a field in the Redis batch object to a value.
    """
    with Redis.pipeline() as pipe:
        while 1:
            try:
                pipe.watch(batch_id)
                batch_struct = json.loads(pipe.get(batch_id))
                pipe.multi()
                batch_struct[subtask][key] = val
                pipe.set(batch_id, json.dumps(batch_struct))
                pipe.execute()
                break
            except WatchError:
                continue


class NidabaTask(Task):
    """
    An abstract class propagating unused function arguments through the
    execution chain. This means that no task should accept arbitrary
    (\*\*kwargs) arguments as they won't be forwarded to the actual function
    and will be retained through the whole chain.
    """
    abstract = True
    acks_late = True
    
    # a dictionary containing all keyword arguments to the task including valid
    # values
    arg_values = {}

    def get_valid_args(self):
        return self.arg_values

    def __call__(self, *args, **kwargs):

        # if args is a dictionary we merge it into kwargs
        if len(args) == 1 and isinstance(args[0], dict):

            kwargs.update(args[0])
            args = ()
            # after a step the output of all tasks is merged into a single
            # argument (indicated by the doc argument being a list of dicts)
            # which we have to unravel first before it can be used be
            # subsequent tasks.
            if isinstance(kwargs['doc'][0], dict):
                docs = []
                for o in kwargs['doc']:
                    docs.append(tuple(o['doc']))
                kwargs['doc'] = docs

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
        task_id = tracking_kwargs['task_id']
        batch_id = tracking_kwargs['batch_id']
        try:
            _redis_set_atomically(batch_id, task_id, 'state', 'RUNNING')
            ret = super(NidabaTask, self).__call__(*args, **nkwargs)
        except:
            exc_info = sys.exc_info()
            exc = traceback.format_exception_only(*exc_info[:2])[-1].strip()
            tb = ''.join(traceback.format_tb(exc_info[-1]))
            _redis_set_atomically(batch_id, task_id, 'errors', (nkwargs, exc, tb))
            _redis_set_atomically(batch_id, task_id, 'state', 'FAILURE')
            raise
        _redis_set_atomically(batch_id, task_id, 'state', 'SUCCESS')

        if isinstance(ret, dict):
            doc = ret.pop('doc')
            if ret:
                _redis_set_atomically(batch_id, task_id, 'misc', ret)
            ret = doc
        _redis_set_atomically(batch_id, task_id, 'result', ret)
        return ret
