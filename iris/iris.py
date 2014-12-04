#! /usr/bin/env python
# -*- coding: utf-8 -*-
# This modul contains all entry points to the various components of iris.

from . import tasks
from . import storage

from irisexceptions import IrisInputException
from itertools import product
from celery import Celery
from celery import chain
from celery import group
from celery.result import AsyncResult, GroupResult
from celery.states import state, PENDING, SUCCESS, FAILURE

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
            * actions: A list of list of lists (containing dicts) defining
            transformations run on input_files. Each middle sublist is taken as
            commands that should be run in parallel. The output of each of
            these commands is fed into the next sublist. The outermost list
            contain sublists which are supposed to run sequentially, i.e. each
            sublist is run after all tasks of the previous sublist have been
            executed. 
            For example [[[{'a'}, {'b'}], [{'c'}], [{'d'}, {'e'}]][[{'f'}]]] is
            expanded to the following (parallel) execution chains:
                ('a' -> 'c' -> 'd')
                ('a' -> 'c' -> 'e')
                ('b' -> 'c' -> 'd')
                ('b' -> 'c' -> 'e')

            After these are run their output is aggregated an 'f' is run.

            Refer to the documentation of the ```tasks``` submodule for further
            information.
    """
    if u'input_files' not in config:
        raise IrisInputException('No input documents given.')
    if u'actions' not in config:
        raise IrisInputException('No actions given.')
    if u'batch_id' not in config:
        raise IrisInputException('No batch ID given.')

    chains = []
    for doc in config[u'input_files']:
        groups = []
        res = []
        for sequence in product([doc], *config[u'actions'][0]):
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
        chains.append(chain(groups))
    rets = []
    for ch in chains:
        rets.append(ch.apply_async().id)
    storage.write_content(config[u'batch_id'], u'.subtasks', u'\n'.join(rets))
    return config[u'batch_id']

def get_state(batch_id):
    if not storage.is_valid_job(batch_id):
        return 'UNKNOWN'
    subtasks = storage.retrieve_content(batch_id, u'.subtasks')[u'.subtasks']
    st = state(SUCCESS)
    for id in subtasks.split('\n'):
        if AsyncResult(id).state < st:
            st = AsyncResult(id).state
    return st

def get_results(batch_id):
    if not storage.is_valid_job(batch_id):
        return 'UNKNOWN'
    subtasks = storage.retrieve_content(batch_id, u'.subtasks')[u'.subtasks']
    outfiles = []
    for id in subtasks.split('\n'):
        ch = AsyncResult(id)
        if ch.successful():
            if type(ch.result[0]) == list:
                outfiles.extend([tuple(x) for x in ch.result])
            else:
                outfiles.append(tuple(ch.result))
    return outfiles
