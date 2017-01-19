# -*- coding: utf-8 -*-
"""
nidaba.tasks.util
~~~~~~~~~~~~~~~~~

Various utility tasks that either can't be classified by purpose or are one of
a kind.

"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba.tasks.helper import NidabaTask
from nidaba.celery import app

from celery import signature, group

@app.task(bind=True, name='nidaba.util.barrier')
def barrier(self, data, merging=False, replace=None):
    replacement = []
    # merge output from same source documents
    if merging == 'doc':
        for docs, task in zip(_group_by_prefix(data), task):
            task['args'] = [docs]
            replacement.append(signature(task))
    # merge everything
    elif merging:
        for task in replace:
            task['args'] = [data]
            replacement.append(signature(task))
    else:
        for ret_val, task in zip(data, replace):
            print(ret_val)
            task['args'] = [ret_val]
            replacement.append(signature(task))
    raise self.replace(group(replacement))
