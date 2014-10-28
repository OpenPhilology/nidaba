#! /usr/bin/env python
# -*- coding: utf-8 -*-
# This modul contains all entry points to the various components of iris.

from . import tasks
from irisexceptions import IrisInputException

from itertools import product
from celery import Celery
from celery import chain
from celery import group
from celery.result import AsyncResult

import sys

def batch(config):
    """Creates a series of celery tasks OCRing a set of documents (among other
    things).
    
    Args:
        config: An object defining a set of documents and a list of actions to
            be applied to these documents

            Required fields are:

            * input_files: A list of image paths
            * batch_id: A globally unique identifier for this batch
            * actions: A list of lists (containing dicts) defining
            transformations run on input_files. Each sublist is taken as
            commands that should be run in parallel. The output of each of
            these commands is fed into the next sublist. For example [[{'a'},
            {'b'}], [{'c'}], [{'d'}, {'e'}]] is expanded to the following (parallel)
            execution chains:
                ('a' -> 'c' -> 'd')
                ('a' -> 'c' -> 'e')
                ('b' -> 'c' -> 'd')
                ('b' -> 'c' -> 'e')

            The following actions are possible:
                * rgb_to_gray
                * binarize
                * dewarp
                * deskew
                * ocr_tesseract
                * ocr_ocropus

            Refer to the documentation of the ```tasks``` submodule for further
            information.
    """
    if u'input_files' not in config:
        raise IrisInputException('No input documents given.')
    if u'actions' not in config:
        raise IrisInputException('No actions given.')
    if u'batch_id' not in config:
        raise IrisInputException('No batch ID given.')

    groups = []
    res = []
    # first sequence contains the input files 
    for sequence in product(config[u'input_files'], *config[u'actions'][0]):
        method = getattr(tasks, sequence[1]['method'])
        ch = chain(method.s((config['batch_id'], sequence[0]), **(sequence[1])))
        for seq in sequence[2:]:
            method = getattr(tasks, seq['method'])
            ch |= method.s(**seq)
        res.append(ch)
    groups.append(group(res))
    groups.append(tasks.sync.s())
    if len(config[u'actions']) > 1:
        for tset in config[u'actions'][1:]:
            res = []
            for sequence in product(*tset):
                method = getattr(tasks, sequence[0]['method'])
                ch = chain(method.s(**(sequence[0])))
                for seq in sequence[1:]:
                    method = getattr(tasks, seq['method'])
                    ch |= method.s(**seq)
                res.append(ch)
            groups.append(group(res))
            groups.append(tasks.sync.s())
    r = chain(groups).apply_async()
    return r.id

def get_progress(task_id):
    r = AsyncResult(task_id)
    return (r.completed_count(), len(r.subtasks))

def get_results(task_id):
    r = AsyncResult(task_id)
    if r.ready() and r.successful():
        return r.result
    else:
        return None
