# -*- coding: utf-8 -*-
"""
nidaba.nidaba
~~~~~~~~~~~~~

The public API of nidaba. External applications should exclusively use the
objects and methods defined here.
"""

from __future__ import absolute_import

from nidaba import tasks
from nidaba import celery
from nidaba import storage
from nidaba.nidabaexceptions import (NidabaInputException,
                                     NidabaNoSuchAlgorithmException,
                                     NidabaTickException, NidabaStepException)

from itertools import product
from celery import chain
from celery import group
from celery.result import AsyncResult
from celery.states import state

import json


class Batch(object):

    """
    Creates a series of celery tasks OCRing a set of documents (among other
    things).

    A batch contains three level of definitions: tasks, ticks, and steps. A
    task is a singular operation on an input document, creating a single output
    document, e.g. binarization using a particular configuration of an
    algorithm or OCR using a particular engine. Multiple tasks executing in
    parallel are grouped into a tick and multiple ticks (running sequentially)
    are grouped into steps which again are executed sequentially.

    The need for steps and ticks arises from two different execution orders
    required by a pipeline. Take the following example:

        step 1:
            tick a: task 1
            tick b: task 2, task 3
            tick c: task 4, task 5

    The pipeline expands this example to the following sequences run in
    parallel (dot product of all ticks):

        task 1 -> task 2 -> task 4
        task 1 -> task 2 -> task 5
        task 1 -> task 3 -> task 4
        task 1 -> task 3 -> task 5

    It is not garantueed that any particular task in another sequence has
    executed successfully before a task in a sequence is run, i.e. it is not
    ensured that all task 1's have finished before task 2 of the first sequence
    is executed, except the task(s) further up the sequence.

    Steps on the other hand ensure that all tasks of the previous step have
    finished successfully. The output(s) of the expanded ticks is aggregated
    into a single list and used as the input of the first tick of the step.
    Expanding on the example the following step is added:

        step 2:
            tick d: task 6

    After the 4 sequence are finished their output is aggregated into a list
    [d1, d2, d3, d4] and used as the input of task 6. The final output of task
    6 is the output of the pipeline.

    The call order to create this example is:

        Batch.add_step()
        Batch.add_tick()
        Batch.add_task(task_1)
        Batch.add_tick()
        Batch.add_task(task_2)
        Batch.add_task(task_3)
        Batch.add_tick()
        Batch.add_task(task_4)
        Batch.add_task(task_5)
        Batch.add_step()
        Batch.add_tick()
        Batch.add_task(task_6)
    """

    def __init__(self, id):

        self.id = id
        self.docs = []
        self.batch_def = []
        self.cur_step = None
        self.cur_tick = None

    def get_state(self):
        """Retrieves the current state of a batch.

        Returns:
            (unicode): A string containing one of the following states:

                NONE: The batch ID is not registered in the backend.
                FAILURE: Batch execution has failed.
                PENDING: The batch is currently running.
                SUCCESS: The batch has completed successfully.
        """
        batch = celery.app.backend.get(self.id)
        try:
            batch = json.loads(batch)
        except Exception:
            return u'NONE'
        if len(batch['errors']) > 0:
            return u'FAILURE'

        st = state('SUCCESS')
        for id in batch['task_ids']:
            if AsyncResult(id).state < st:
                st = AsyncResult(id).state
        return unicode(st)

    def get_errors(self):
        """
        Retrieves all errors of the batch.

        Returns:
            list: A list of tuples containing

                args kwargs exception_message

            of the failing task or None if there are no errors.
        """
        batch = celery.app.backend.get(self.id)
        try:
            batch = json.loads(batch)
        except Exception:
            return None
        if len(batch['errors']) > 0:
            return batch['errors']

        return None

    def get_results(self):
        """
        Retrieves the storage tuples of a successful batch or None.

        Returns:
            list: A list of storage tuples or None if no results are available.
        """
        batch = celery.app.backend.get(self.id)
        try:
            batch = json.loads(batch)
        except Exception:
            return None

        if self.get_state() != 'SUCCESS':
            return None

        outfiles = []
        for id in batch['task_ids']:
            ch = AsyncResult(id)
            if ch.successful():
                if isinstance(ch.result[0], list):
                    outfiles.extend([tuple(x) for x in ch.result])
                else:
                    outfiles.append(tuple(ch.result))
        return outfiles

    def add_document(self, doc):
        """Add a document to the batch.

        Adds a document tuple to the batch and checks if it exists.

        Args:
            doc (tuple): A standard document tuple.

        Raises:
            NidabaInputException: The document tuple does not refer to a file.
        """

        if not storage.is_file(*doc):
            raise NidabaInputException('Input document is not a file.')
        self.docs.append(doc)

    def add_task(self, method, **kwargs):
        """Add a task to the current tick.

        Adds a ``task``, a single executable task gathering one or more input
        documents and returning a single output document, to the current tick.
        Multiple jobs are run in parallel.

        Args:
            method (unicode): A task identifier
            **kwargs: Arguments to the task

        Raises:
            NidabaTickException: There is no tick to add a task to.
            NidabaNoSuchAlgorithmException: Invalid method given.
        """
        if self.cur_tick is None:
            raise NidabaTickException('No tick to add task to.')
        if u'nidaba.' + method not in celery.app.tasks:
            raise NidabaNoSuchAlgorithmException('No such task in registry')
        kwargs[u'method'] = method
        kwargs[u'id'] = self.id
        self.cur_tick.append(kwargs)

    def add_tick(self):
        """Add a new tick to the current step.

        Adds a ``tick``, a set of tasks running in parallel and sharing common
        input documents to the current step.

        Raises:
            NidabaStepException: There is no step to add a tick to.
        """
        if self.cur_step is None:
            raise NidabaStepException('No step to add tick to.')
        if self.cur_tick:
            self.cur_step.append(self.cur_tick)
        self.cur_tick = []

    def add_step(self):
        """Add a new step to the batch definition.

        Adds a ``step``, a list of sequentially run ticks to the batch
        definition. The output(s) of the last tick of a step is aggregated into
        a single list and used as the input of the first tick of the following
        step.
        """
        if self.cur_tick:
            self.cur_step.append(self.cur_tick)
            self.cur_tick = []
        if self.cur_step:
            self.batch_def.append(self.cur_step)
        self.cur_step = []

    def run(self):
        """Executes the current batch definition.

        Expands the current batch definition to a series of celery chords and
        executes them asynchronously. Additionally a batch record is written to
        the celery result backend.

        Returns:
            (unicode): Batch identifier.
        """
        # flush most recent tick/step onto the batch definition
        self.add_tick()
        self.add_step()

        groups = []
        tick = []
        # We first expand the tasks starting from the second step as these are
        # the same for each input document.
        if len(self.batch_def) > 1:
            groups.append(tasks.util.sync.s())
            for tset in self.batch_def[1:]:
                for sequence in product(*tset):
                    method = celery.app.tasks[
                        'nidaba.' + sequence[0]['method']]
                    ch = chain(method.s(**(sequence[0])))
                    for seq in sequence[1:]:
                        method = celery.app.tasks['nidaba.' + seq['method']]
                        ch |= method.s(**seq)
                    tick.append(ch)
                groups.append(group(tick))
                groups.append(tasks.util.sync.s())

        # The expansion steps described above is redone for each input document
        rets = []
        for doc in self.docs:
            tick = []
            # the first step is handled differently as the input document has
            # to be added explicitely.
            for sequence in product([doc], *self.batch_def[0]):
                method = celery.app.tasks['nidaba.' + sequence[1]['method']]
                ch = chain(method.s(doc=sequence[0], **(sequence[1])))
                for seq in sequence[2:]:
                    method = celery.app.tasks['nidaba.' + seq['method']]
                    ch |= method.s(**seq)
                tick.append(ch)
            rets.append(
                chain([group(tick)] + [tasks.util.sync.s()] +
                      groups[:-1]).apply_async(kwargs={'root': doc}).id)
        celery.app.backend.set(
            self.id, json.dumps({'errors': [], 'task_ids': rets}))
        return self.id
