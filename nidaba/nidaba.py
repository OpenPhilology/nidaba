# -*- coding: utf-8 -*-
"""
nidaba.nidaba
~~~~~~~~~~~~~

The public API of nidaba. External applications should exclusively use the
objects and methods defined here.
"""

from __future__ import absolute_import

from nidaba import tasks
from nidaba import plugins
from nidaba import celery
from nidaba import storage
from nidaba import config
from nidaba.nidabaexceptions import (NidabaInputException,
                                     NidabaNoSuchAlgorithmException,
                                     NidabaTickException, NidabaStepException)

from itertools import product
from celery import chain
from celery import group
from celery.result import AsyncResult
from celery.states import state

import json
import uuid
import redis

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
        r = config.Redis
        batch = r.get(self.id)
        try:
            batch = json.loads(batch)
        except Exception:
            return u'NONE'
        st = 'SUCCESS'
        for subtask in batch.itervalues():
            if subtask['state'] == 'PENDING' or subtask['state'] == 'RUNNING':
                st = u'PENDING'
            if subtask['state'] == 'FAILURE':
                return u'FAILURE'
        return st

    def get_errors(self):
        """
        Retrieves all errors of the batch.

        Returns:
            list: A list of tuples containing keyword arguments to the task, a
            dictionary containing debug tracking information (i.e. variables
            which are given to the tasks as keyword arguments but aren't
            arguments to the underlying function), and the exception message of
            the failure.
        """
        batch = celery.app.backend.get(self.id)
        try:
            batch = json.loads(batch)
        except:
            return None
        if len(batch['errors']) > 0:
            return batch['errors']

        return None

    def get_results(self):
        """
        Retrieves the storage tuples of a successful batch.

        Returns:
        """
        batch = config.Redis.get(self.id)
        try:
            batch = json.loads(batch)
        except Exception:
            return None

        if self.get_state() != 'SUCCESS':
            return None

        outfiles = []
        for subtask in batch.itervalues():
            if len(subtask['children']) == 0 and not subtask['housekeeping']:
                outfiles.append((subtask['result'], subtask['root_document']))
        return outfiles

    def get_extended_state(self):
        """
        Returns extended batch state information.

        Returns:
            A dictionary containing an entry for each subtask.
        """
        return json.loads(config.Redis.get(self.id))

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

        Expands the current batch definition to a series of celery chains and
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

        result_data = {}

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
        chains = []
        for doc in self.docs:
            tick = []
            # the first step is handled differently as the input document has
            # to be added explicitely.
            for sequence in product([doc], *self.batch_def[0]):
                method = celery.app.tasks['nidaba.' + sequence[1]['method']]
                root = sequence[0]
                ch = chain(method.s(doc=root, **(sequence[1])))
                for seq in sequence[2:]:
                    method = celery.app.tasks['nidaba.' + seq['method']]
                    ch |= method.s(**seq)
                tick.append(ch)
            doc_group = group(tick)
            parents = []
            group_list = [doc_group] + groups
            chains.append(chain(group_list))

            # Now we give out another set of unique task identifiers and save
            # them to the database. Presetting the celery task ID does not work
            # as our chains get automagically upgraded to chords by celery,
            # erasing the ID fields in the process.
            for step in enumerate(group_list):
                if hasattr(step[1], 'tasks'):
                    for tick in enumerate(step[1].tasks):
                        if step[0]:
                            parents = parent_step
                        else:
                            parents = []
                        for task in enumerate(tick[1].tasks):
                            task_id = uuid.uuid4().get_hex()
                            result_data[task_id] = {
                                'children': [],
                                'parents': parents,
                                'housekeeping': False,
                                'root_document': doc,
                                'state': 'PENDING',
                                'result': None,
                                'task': (task[1]['task'], task[1]['kwargs']),
                            }
                            for parent in parents:
                                result_data[parent]['children'] = task_id
                            group_list[step[0]].tasks[tick[0]].tasks[task[0]].kwargs['task_id'] = task_id
                            group_list[step[0]].tasks[tick[0]].tasks[task[0]].kwargs['batch_id'] = self.id
                            parents = [task_id]
                    parent_step = [x.tasks[-1].kwargs['task_id'] for x in
                                   step[1].tasks]
                else:
                    task_id = uuid.uuid4().get_hex()
                    result_data[task_id] = {
                        'children': [],
                        'parents': [],
                        'housekeeping': True,
                        'root_document': doc,
                        'state': 'PENDING',
                        'result': None,
                        'task': (task[1]['task'], task[1]['kwargs']),
                    }
                    group_list[step[0]].kwargs['task_id'] = task_id
                    group_list[step[0]].kwargs['batch_id'] = self.id
        r = config.Redis
        r.set(self.id, json.dumps(result_data))
        [x.apply_async() for x in chains]
        return self.id
