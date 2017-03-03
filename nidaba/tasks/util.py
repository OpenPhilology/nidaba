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

from celery import signature, group, chain
from itertools import cycle, izip

@app.task(bind=True, name='nidaba.util.barrier')
def barrier(self, data, merging=False, sequential=False, replace=None):
    replacement = []
    # merge output from same source documents
    if merging == 'doc':
        for docs, task in izip(cycle(_group_by_prefix(data)), task):
            if sequential:
                task[0]['args'] = [docs]
                replacement.append(chain(signature(t) for t in task))
            else:
                task['args'] = [docs]
                replacement.append(signature(task))
    # merge everything
    elif merging:
        for task in replace:
            if sequential:
                task[0]['args'] = [data]
                replacement.append(chain(signature(t) for t in task))
            else:
                task['args'] = [data]
                replacement.append(signature(task))
    else:
        for ret_val, task in izip(cycle(data), replace):
            if sequential:
                task[0]['args'] = [ret_val]
                replacement.append(chain(signature(t) for t in task))
            else:
                task['args'] = [ret_val]
                replacement.append(signature(task))
    raise self.replace(group(replacement))
