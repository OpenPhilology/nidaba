# -*- coding: utf-8 -*-
"""
nidaba.nidaba
~~~~~~~~~~~~~

The public API of nidaba. External applications should exclusively use the
objects and methods defined here.
"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba import tasks
from nidaba import plugins
from nidaba import celery
from nidaba import storage
from nidaba import config
from nidaba.nidabaexceptions import (NidabaInputException,
                                     NidabaNoSuchAlgorithmException,
                                     NidabaTickException, NidabaStepException)

from celery import chain
from celery import group
from itertools import product
from inspect import getcallargs
from collections import OrderedDict
from requests_toolbelt.multipart import encoder

import os
import json
import uuid
import requests


def task_arg_validator(arg_values, **kwargs):
    """
    Validates keyword arguments against the list of valid argument values
    contained in the task definition.

    Raises:
        NidabaInputException if validation failed.
    """
    kwc = kwargs.copy()

    def _val_single_arg(arg, type):
        if type == 'float':
            if not isinstance(val, float):
                raise NidabaInputException('{} is not a float'.format(val))
        elif type == 'int':
            if not isinstance(val, int):
                raise NidabaInputException('{} is not an int'.format(val))
        elif type == 'str':
            if not isinstance(val, basestring):
                raise NidabaInputException('{} is not a string'.format(val))
        else:
            raise NidabaInputException('Argument type {} unknown'.format(type))

    for k, v in arg_values.iteritems():
        try:
            val = kwc.pop(k)
        except:
            raise NidabaInputException('Missing argument: {}'.format(k))
        if isinstance(v, tuple):
            if not isinstance(val, v[0]):
                raise NidabaInputException('{} of different type than range fields'.format(val))
            if val < v[0] or val > v[1]:
                raise NidabaInputException('{} outside of allowed range {}-{}'.format(val, *v))
        elif isinstance(v, list):
            if val not in v:
                raise NidabaInputException('{} not in list of valid values'.format(val))
        else:
            _val_single_arg(val, v)

    if kwc:
        raise NidabaInputException('Superfluous arguments present')


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
        self.scratchpad = {}
        self.redis = config.Redis


    def add_scratchpad(self):
        """
        Adds a scratchpad to the database that allows suspending and resuming
        task assembly. 
        
        All added documents and tasks will be stored persistently;
        reinstantiating the Batch object and calling restore_scratchpad will
        restore the object to the previous state.

        The scratchpad will be destroyed on task execution.

        Raises:
            NidabaInputException if a scratchpad is already attached or the
            batch has been executed.
        """
        if self.redis.get(self.id) is not None:
            raise NidabaInputException('Batch already has scratchpad or been '
                                       'executed.')
        else:
            self.scratchpad = {'scratchpad': {'docs': self.docs, 
                                              'batch_def': self.batch_def,
                                              'cur_step': self.cur_step,
                                              'cur_tick': self.cur_tick}}
            self.redis.set(self.id, json.dumps(self.scratchpad))

    def restore_scratchpad(self):
        """
        Retrieves the scratchpad from the database and restores its contents
        to the current Batch object overwriting any information defined in it.

        Raises:
            NidabaInputException if no scratchpad can be found either because
            none has been attached or the batch has already been executed.
        """
        scratch = json.loads(self.redis.get(self.id))
        if scratch and 'scratchpad' in scratch:
            self.scratchpad = scratch
            for k, v in self.scratchpad['scratchpad'].iteritems():
                setattr(self, k, v)
        else:
            raise NidabaInputException('No scratchpad in database')

    def get_state(self):
        """
        Retrieves the current state of a batch.

        Returns:
            (unicode): A string containing one of the following states:

                NONE: The batch ID is not registered in the backend.
                FAILURE: Batch execution has failed.
                PENDING: The batch is currently running.
                SUCCESS: The batch has completed successfully.
        """
        batch = self.redis.get(self.id)
        try:
            batch = json.loads(batch)
        except Exception:
            return u'NONE'
        if 'scratchpad' in batch:
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
        batch = self.redis.get(self.id)
        try:
            batch = json.loads(batch)
        except:
            return None
        errors = []
        for subtask in batch.itervalues():
            if subtask['state'] == 'FAILURE':
                errors.append(subtask)
        return errors

    def get_results(self):
        """
        Retrieves the storage tuples of a successful batch.

        Returns:
        """
        batch = self.redis.get(self.id)
        try:
            batch = json.loads(batch)
        except Exception:
            return None

        outfiles = []
        for subtask in batch.itervalues():
            if len(subtask['children']) == 0 and not subtask['housekeeping'] and subtask['result'] is not None:
                outfiles.append((subtask['result'], subtask['root_document']))
        return outfiles

    def get_extended_state(self):
        """
        Returns extended batch state information.

        Returns:
            A dictionary containing an entry for each subtask.
        """
        state = json.loads(self.redis.get(self.id))
        if 'scratchpad' in state:
            return []
        else:
            return state

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
        if self.scratchpad:
            self.scratchpad['scratchpad']['docs'] = self.docs
            self.redis.set(self.id, json.dumps(self.scratchpad))

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
        if self.scratchpad:
            self.scratchpad['scratchpad']['cur_tick'].append(kwargs)
            self.redis.set(self.id, json.dumps(self.scratchpad))


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
        if self.scratchpad:
            self.scratchpad['scratchpad']['cur_step'] = self.cur_step
            self.scratchpad['scratchpad']['cur_tick'] = []
            self.redis.set(self.id, json.dumps(self.scratchpad))


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
        if self.scratchpad:
            self.scratchpad['scratchpad']['cur_step'] = self.cur_step
            self.scratchpad['scratchpad']['cur_tick'] = self.cur_tick
            self.scratchpad['scratchpad']['batch_def'] = self.batch_def
            self.redis.set(self.id, json.dumps(self.scratchpad))


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
                    method = celery.app.tasks['nidaba.' +
                                              sequence[0]['method']]
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
        # also deletes the scratchpad 
        self.redis.set(self.id, json.dumps(result_data))
        [x.apply_async() for x in chains]
        return self.id


class SimpleBatch(Batch):
    """
    A simpler interface to the batch functionality that is more amenable to
    RESTful task assembly and prevents some incidences of
    bullet-in-foot-syndrome.

    A SimpleBatch contains only a list of input documents and a series of
    tasks. The order of task execution depends on a predefined order, similar
    to the ``nidaba`` command-line util. 

    If no batch identifier is given a new batch will be created.

    SimpleBatches always contain a scratchpad (which will be restored
    automatically).
    """
    def __init__(self, id=None):
        if id is None:
            id = unicode(uuid.uuid4())
            storage.prepare_filestore(id)
        if not storage.is_valid_job(id):
            raise NidabaInputException('Storage not prepared for task')
        super(SimpleBatch, self).__init__(id)
        self.lock = False
        self.tasks = OrderedDict({'img': [], 
                                  'binarize': [],
                                  'segmentation': [], 
                                  'ocr': [],
                                  'stats': [], 
                                  'postprocessing': [],
                                  'output': []})

        try:
            self.add_scratchpad()
            self.scratchpad['scratchpad']['tasks'] = self.tasks
            self.redis.set(self.id, json.dumps(self.scratchpad))
        except:
            try:
                self.restore_scratchpad()
            except NidabaInputException:
                # no scratchpad in database means batch is running and may not
                # be modified.
                self.lock = True

    def is_running(self):
        """
        Returns True if the batch's run() method has been successfully called, otherwise False.
        """
        return self.lock

    def get_tasks(self):
        """
        Returns the simplified task definition either from the scratchpad or
        from the pipeline when already in execution.
        """
        entry = json.loads(self.redis.get(self.id))
        if 'scratchpad' in entry:
            scratch = json.loads(self.redis.get(self.id))
            return scratch['scratchpad']['tasks']
        else:
            state = super(SimpleBatch, self).get_extended_state()
            tasks = OrderedDict({'img': [], 
                                 'binarize': [],
                                 'segmentation': [], 
                                 'ocr': [],
                                 'stats': [], 
                                 'postprocessing': [],
                                 'output': []})
            for task in state.itervalues():
                _, group, method = task['task'][0].split('.')
                if group in tasks:
                    tasks[group].append(('{}.{}'.format(group, method),
                                         task['task'][1]))
            return tasks

    def get_documents(self):
        """
        Returns the list of input document for this task.
        """
        entry = json.loads(self.redis.get(self.id))
        if 'scratchpad' in entry:
            return entry['scratchpad']['docs']
        else:
            state = super(SimpleBatch, self).get_extended_state()
            docs = []
            for task in state.itervalues():
                if task['root_document'] not in docs:
                    docs.append(task['root_document'])
            return docs

    @staticmethod
    def get_available_tasks():
        """
        Returns all available tasks and their valid argument values.

        The return value is an ordered dictionary containing an entry for each
        group with a sub-dictionary containing the task identifiers and valid
        argument values.
        """
        tasks = OrderedDict()
        for task, fun in celery.app.tasks.iteritems():
            try:
                _, group, method = task.split('.')
            except:
                continue
            if group not in tasks:
                tasks[group] = {}
            kwargs = fun.get_valid_args()
            tasks[group][method] = kwargs
        return tasks

    def add_document(self, doc):
        """Add a document to the batch.

        Adds a document tuple to the batch and checks if it exists.

        Args:
            doc (tuple): A standard document tuple.

        Raises:
            NidabaInputException: The document tuple does not refer to a file
                                  or the batch is locked because the run()
                                  method has been called.
        """
        if self.lock:
            raise NidabaInputException('Executed batch may not be modified')
        super(SimpleBatch, self).add_document(doc)


    def add_task(self, group, method, **kwargs):
        """
        Add a particular task configuration to a task group.

        Args:
            group (unicode): Group the task belongs to
            method (unicode): Name of the task
            kwargs: Arguments to the task
        """

        if self.lock:
            raise NidabaInputException('Executed batch may not be modified')
        # validate that the task exists
        if group not in self.tasks:
            raise NidabaNoSuchAlgorithmException('Unknown task group')
        if u'nidaba.{}.{}'.format(group, method) not in celery.app.tasks:
            raise NidabaNoSuchAlgorithmException('Unknown task')
        task = celery.app.tasks[u'nidaba.{}.{}'.format(group, method)]
        # validate arguments first against getcallargs
        try:
            getcallargs(task.run, ('', ''), **kwargs)
        except TypeError as e:
            raise NidabaInputException(str(e))
        # validate against arg_values field of the task
        task_arg_validator(task.get_valid_args(), **kwargs)
        self.tasks[group].append((u'{}.{}'.format(group, method), kwargs))
        self.scratchpad['scratchpad']['tasks'] = self.tasks
        self.redis.set(self.id, json.dumps(self.scratchpad))


    def run(self):
        """Executes the current batch definition.

        Expands the current batch definition to a series of celery chains and
        executes them asynchronously. Additionally a batch record is written to
        the celery result backend.

        Returns:
            (unicode): Batch identifier.
        """
        if self.lock:
            raise NidabaInputException('Executed batch may not be modified')

        self.add_step()
        for _, btasks in self.tasks.iteritems():
            self.add_tick()
            for task in btasks:
                super(SimpleBatch, self).add_task(task[0], **task[1])
        self.lock = True
        return super(SimpleBatch, self).run()


class NetworkSimpleBatch(object):
    """
    A SimpleBatch object providing the same interface as a SimpleBatch.

    It does some basic error checking to minimize network traffic but it won't
    catch all errors before issuing API requests, especially if the batch is
    modified by another process. In these cases exceptions will be raised by
    the ``requests`` module.
    """
    def __init__(self, host, id=None):
        self.id = id
        self.host = host
        self.lock = False
        self.allowed_tasks = {}
        if id is not None:
            r = requests.get('{}/batch/{}'.format(host, id))
            r.raise_for_status()


    def create_batch(self):
        """
        Creates a batch on the server. Also synchronizes the list of available
        tasks and their parameters.
        """
        if self.id is not None:
            raise NidabaInputException('SimpleBatch object already initialized')
        r = requests.post('{}/batch'.format(self.host))
        r.raise_for_status()
        self.id = r.json()['id']
        self.lock = False
        self.get_available_tasks()
        return self.id

    def get_available_tasks(self):
        """
        Synchronizes the local task/parameter list with the remote server.
        """
        r = requests.get('{}/tasks'.format(self.host))
        r.raise_for_status()
        self.allowed_tasks = r.json()

    def is_running(self):
        """
        Returns True if the batch's run() method has been successfully called, otherwise False.
        """
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        r = requests.get('{}/batch/{}'.format(self.host, self.id))
        r.raise_for_status()
        self.lock = True
        if r.json():
            self.lock = True
            return True
        else:
            self.lock = False
            return False

    def get_tasks(self):
        """
        Returns the task tree either from the scratchpad or from the pipeline
        when already in execution.
        """
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        r = requests.get('{}/batch/{}/tasks'.format(self.host, self.id))
        r.raise_for_status()
        return r.json()

    def get_documents(self):
        """
        Returns the list of input document for this task.
        """
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        r = requests.get('{}/batch/{}/pages'.format(self.host, self.id))
        r.raise_for_status()
        return r.json()

    def add_document(self, path, callback, auxiliary=False):
        """Add a document to the batch.

        Uploads a document to the API server and adds it to the batch.

        ..note::
            Note that this function accepts a standard file system path and NOT
            a storage tuple as a client using the web API is not expected to
            keep a separate, local storage medium.

        Args:
            path (unicode): Path to the document
            callback (function): A function that is called with a
                                 ``requests_toolbelt.multipart.encoder.MultipartEncoderMonitor`` 
                                instance.
            auxiliary (bool): Switch to disable setting the file as an input
                              document. May be used to upload ground truths,
                              metadata, and other ancillary files..

        Raises:
            NidabaInputException: The document does not refer to a file or the
                                  batch is locked because the run() method has
                                  been called.
        """
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        if self.lock:
            raise NidabaInputException('Executed batch may not be modified')
        if auxiliary:
            params = {'auxiliary': True}
        else:
            params = {}
        m = encoder.MultipartEncoderMonitor.from_fields(
            fields={'scans': (os.path.basename(path), open(path, 'rb'))},
            callback=callback)
        r = requests.post('{}/batch/{}/pages'.format(self.host, self.id),
                          data=m, headers={'Content-Type': m.content_type},
                          params=params)
        r.raise_for_status()
        return r.json()[0]['url']

    def add_task(self, group, method, *args, **kwargs):
        """
        Add a particular task configuration to a task group.

        Args:
            group (unicode): Group the task belongs to
            method (unicode): Name of the task
            kwargs: Arguments to the task
        """
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        if self.lock:
            raise NidabaInputException('Executed batch may not be modified')
        # validate that the task exists
        if group not in self.allowed_tasks or method not in self.allowed_tasks[group]:
            raise NidabaInputException('Unknown task {}'.format(method))
        args = self.allowed_tasks[group][method]
        # validate against arg_values field of the task
        task_arg_validator(args, **kwargs)
        r = requests.post('{}/batch/{}/tasks/{}/{}'.format(self.host, self.id,
                                                           group, method),
                          data=kwargs)  
        r.raise_for_status()

    def get_extended_state(self):
        """
        Returns the extended batch state.

        Raises:
            NidabaInputException if the batch hasn't been executed yet.
        """
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        r = requests.get('{}/batch/{}'.format(self.host, self.id))
        r.raise_for_status()
        if 'chains' in r.json():
            self.lock = True
            return r.json()['chains']

    def run(self):
        """
        Executes the current batch definition.

        Expands the current batch definition to a series of celery chains and
        executes them asynchronously. Additionally a batch record is written to
        the celery result backend.

        Returns:
            (unicode): Batch identifier.
        """
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        if self.lock:
            raise NidabaInputException('Executed batch may not be reexecuted')
        r = requests.post('{}/batch/{}'.format(self.host, self.id))
        r.raise_for_status()
        return self.id
