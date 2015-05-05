# -*- coding: utf-8 -*-
"""
nidaba.tasks.util
~~~~~~~~~~~~~~~~~

Various utility tasks that either can't be classified by purpose or are one of
a kind.

"""

from __future__ import absolute_import

from nidaba.tasks.helper import NidabaTask
from nidaba.celery import app


@app.task(base=NidabaTask, name=u'nidaba.util.sync')
def sync(doc):
    """
    Takes ones argument and returns it. Used to synchronized stuff as
    chaining groups is not possible with the current celery version.

    Args:
        doc: An arbitrary input argument

    Returns:
        The input argument unaltered
    """
    return doc
