# -*- coding: utf-8 -*-
"""
nidaba.nidaba
~~~~~~~~~~~~~

The public API of nidaba. External applications should exclusively use the
objects and methods defined here.
"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba.nidabaexceptions import (NidabaInputException,
                                     NidabaNoSuchAlgorithmException,
                                     NidabaTickException, NidabaStepException)

from celery import chord, chain
from inspect import getcallargs
from collections import OrderedDict, Iterable
from requests_toolbelt.multipart import encoder
from redis import WatchError

import os
import json
import uuid
import requests
import itertools

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
            if not isinstance(val, float) and not isinstance(val, int):
                raise NidabaInputException('{} is not a float'.format(val))
        elif type == 'int':
            if not isinstance(val, int):
                raise NidabaInputException('{} is not an int'.format(val))
        elif type == 'str':
            if not isinstance(val, basestring):
                raise NidabaInputException('{} is not a string'.format(val))
        # XXX: Add file/files checker for local case
        elif type == 'file':
            pass
        elif type == 'files':
            pass
        else:
            raise NidabaInputException('Argument type {} unknown'.format(type))

    for k, v in arg_values.iteritems():
        try:
            val = kwc.pop(k)
        except:
            raise NidabaInputException('Missing argument: {}'.format(k))
        if isinstance(v, tuple):
            if not isinstance(val, type(v[0])):
                raise NidabaInputException('{} of different type than range fields'.format(val))
            if val < v[0] or val > v[1]:
                raise NidabaInputException('{} outside of allowed range {}-{}'.format(val, *v))
        elif isinstance(v, list):
            if isinstance(val, Iterable) and not isinstance(val, basestring):
                va = set(val)
            else:
                va = set([val])
            if not set(v).issuperset(va):
                raise NidabaInputException('{} not in list of valid values'.format(val))
        else:
            _val_single_arg(val, v)

    if kwc:
        raise NidabaInputException('Superfluous arguments present')


class Batch(object):

    """
    Creates a series of celery tasks OCRing a set of documents (among other
    things).

    """

    def __init__(self, id=None):
        # stuff depending on a valid configuration
        from nidaba import storage
        from nidaba import config
        self.storage = storage

        # slowly importing stuff
        from nidaba import tasks
        from nidaba import plugins
        from nidaba import celery
        self.task_reg = tasks
        self.celery = celery

        self.id = id
        if self.id is None:
            self.id = uuid.uuid4().get_hex()
            self.storage.prepare_filestore(self.id)
        if not self.storage.is_valid_job(self.id):
            raise NidabaInputException('Storage not prepared for task')

        self.docs = []
        self.scratchpad = {}
        self.redis = config.Redis

        self.tasks = OrderedDict([('img', []), 
                                  ('binarize', []),
                                  ('segmentation', []), 
                                  ('ocr', []),
                                  ('stats', []), 
                                  ('postprocessing', []),
                                  ('output', []),
                                  ('archive', [])])

        # defines if tasks in a group are run in parallel or in sequence and their merge mode
        self.order = {'img': ('sequence', False),
                      'binarize': ('parallel', False),
                      'segmentation': ('parallel', False),
                      'ocr': ('parallel', False),
                      'stats': ('parallel', False),
                      'postprocessing': ('sequence', 'doc'),
                      'output': ('sequence', False),
                      'archive': ('parallel', True)}

        self.lock = False
        with self.redis.pipeline() as pipe:
            while(1):
                try:
                    pipe.watch(self.id)
                    self._restore_and_create_scratchpad(pipe)
                    if 'scratchpad' not in self.scratchpad:
                        self.lock = True
                    pipe.execute()
                    break
                except WatchError:
                    continue

    def _restore_and_create_scratchpad(self, pipe):
        """
        Restores the scratchpad or creates one if none exists. Does not create
        a scratchpad on an already executed task.
        """
        scratch = pipe.get(self.id)
        if scratch is not None:
            scratch = json.loads(scratch)
            if 'scratchpad' in scratch:
                self.scratchpad = scratch
                for k, v in self.scratchpad['scratchpad'].iteritems():
                    setattr(self, k, v)
                # reorder task definitions
        else:
            self.scratchpad = {'scratchpad': {'docs': self.docs, 
                                              'tasks': self.tasks}}
            pipe.set(self.id, json.dumps(self.scratchpad))

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
            if len(subtask['children']) == 0 and subtask['result'] is not None:
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

    def get_available_tasks(self):
        """
        Returns all available tasks and their valid argument values.

        The return value is an ordered dictionary containing an entry for each
        group with a sub-dictionary containing the task identifiers and valid
        argument values.
        """
        tasks = OrderedDict()
        for task, fun in self.celery.app.tasks.iteritems():
            try:
                _, group, method = task.split('.')
            except:
                continue
            if group == 'util':
                continue
            if group not in tasks:
                tasks[group] = {}
            kwargs = fun.get_valid_args()
            tasks[group][method] = kwargs
        return tasks

    def get_tasks(self):
        """
        Returns the simplified task definition either from the scratchpad or
        from the pipeline when already in execution.
        """
        entry = json.loads(self.redis.get(self.id))
        if 'scratchpad' in entry:
            scratch = json.loads(self.redis.get(self.id))
            return scratch['scratchpad']['simple_tasks']
        else:
            state = self.get_extended_state()
            tasks = OrderedDict([('img', []), 
                                 ('binarize', []),
                                 ('segmentation', []), 
                                 ('ocr', []),
                                 ('stats', []), 
                                 ('postprocessing', []),
                                 ('output', []),
                                 ('output', [])])

            for task in state.itervalues():
                if task['task'][0] in tasks:
                    tasks[task['task'][0]].append(task['task'])
            return tasks

    def get_documents(self):
        """
        Returns the list of input document for this task.
        """
        entry = json.loads(self.redis.get(self.id))
        if 'scratchpad' in entry:
            return entry['scratchpad']['docs']
        else:
            state = self.get_extended_state()
            docs = []
            for task in state.itervalues():
                for doc in task['root_documents']:
                    if doc not in docs:
                        docs.append(doc)
            return docs

    def is_running(self):
        """
        Returns True if the batch's run() method has been successfully called, otherwise False.
        """
        return self.lock

    def add_document(self, doc):
        """Add a document to the batch.

        Adds a document tuple to the batch and checks if it exists.

        Args:
            doc (tuple): A standard document tuple.

        Raises:
            NidabaInputException: The document tuple does not refer to a file.
        """
        if self.lock:
            raise NidabaInputException('Executed batch may not be modified')

        if not self.storage.is_file(*doc):
            raise NidabaInputException('Input document is not a file.')
        
        with self.redis.pipeline() as pipe:
            while(1):
                try:
                    pipe.watch(self.id)
                    self._restore_and_create_scratchpad(pipe)
                    self.docs.append(doc)
                    self.scratchpad['scratchpad']['docs'] = self.docs
                    pipe.set(self.id, json.dumps(self.scratchpad))
                    pipe.execute()
                    break
                except self.redis.WatchError:
                    continue

    def add_task(self, group, method, **kwargs):
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
        if self.lock:
            raise NidabaInputException('Executed batch may not be modified')
        # validate that the task exists
        if group not in self.tasks:
            raise NidabaNoSuchAlgorithmException('Unknown task group {}'.format(group))
        if u'nidaba.{}.{}'.format(group, method) not in self.celery.app.tasks:
            raise NidabaNoSuchAlgorithmException('Unknown task {} {}'.format(group, method))
        task = self.celery.app.tasks[u'nidaba.{}.{}'.format(group, method)]
        # validate arguments first against getcallargs
        try:
            getcallargs(task.run, ('', ''), **kwargs)
        except TypeError as e:
            raise NidabaInputException(str(e))
        # validate against arg_values field of the task
        task_arg_validator(task.get_valid_args(), **kwargs)
        with self.redis.pipeline() as pipe:
            while(1):
                try:
                    pipe.watch(self.id)
                    self._restore_and_create_scratchpad(pipe)
                    self.tasks[group].append((method, kwargs))
                    self.scratchpad['scratchpad']['simple_tasks'] = self.tasks
                    pipe.set(self.id, json.dumps(self.scratchpad))
                    pipe.execute()
                    break
                except WatchError:
                    continue

    def _add_step(self, merging=False):
        """Add a new step to the batch definition.

        A step is a synchronization barrier in the execution graph. It may
        either distribute the output of previous tasks across all subsequent
        tasks (merging=False), run each task with all outputs from a single
        source document (doc), or merge all outputs and run each task on all of
        them (True).

        Args:
            merging (False, True, doc): 
        """
        with self.redis.pipeline() as pipe:
            while(1):
                try:
                    pipe.watch(self.id)
                    self._restore_and_create_scratchpad(pipe)
                    self.tasks.append({'tasks': [], 'merging': merging})
                    self.scratchpad['scratchpad']['tasks'] = self.tasks
                    pipe.set(self.id, json.dumps(self.scratchpad))
                    pipe.execute()
                    break
                except WatchError:
                    continue

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

        # reorder task definitions
        keys = ['img', 'binarize', 'segmentation', 'ocr', 'stats', 'postprocessing', 'output', 'archive']
        tasks = OrderedDict((key, self.tasks[key]) for key in keys)
        first = []
        prev = None
        result_data = {}
        self.lock = True

        # build chain
        root_docs = self.docs
        prev = []
        for group, step in tasks.iteritems():
            # skip groups without tasks
            if not step:
                continue
            sequential = True if self.order[group][0] == 'sequence' else False
            mmode = self.order[group][1]

            def _repeat(lst, n):
                return list(itertools.chain.from_iterable(itertools.repeat(x, n) for x in lst))

            if sequential:
                step = [step]
            # multiply number of tasks in this step by number of tasks in
            # previous step if not merging
            if not mmode:
                step = _repeat(step, len(root_docs))
                root_docs = root_docs * (len(step)/len(root_docs))
            # by number of root docs if doc merging
            elif mmode == 'doc':
                step = _repeat(step, len(self.docs))
                root_docs = self.docs
            else:
                root_docs = [root_docs] * len(step)
            if not sequential:
                step = [[x] for x in step]
            nprev = []
            r = []
            for rd_idx, (rdoc, c) in enumerate(zip(root_docs, step)):
                if sequential:
                    r.append([])
                for idx, (fun, kwargs) in enumerate(c):
                    # if idx > 0 (sequential == true) parent is previous task in sequence
                    if idx > 0:
                        parents = [task_id]
                    # if merge mode is 'doc' base parents are tasks n * (len(prev)/len(docs)) to n+1 ... 
                    elif mmode == 'doc':
                        parents = prev[rd_idx::len(root_docs)]
                    # if merging everything all tasks in previous step are parents
                    elif mmode:
                        parents = prev
                    # if not merging a single task in previous step is the parent
                    elif mmode == False:
                        parents = [prev[rd_idx % len(prev)]] if prev else prev
                    task_id = uuid.uuid4().get_hex()
                    # last task in a sequence is entered into new prev array
                    if idx+1 == len(c):
                        nprev.append(task_id)
                    result_data[task_id] = {
                       'children': [],
                       'parents': parents,
                       'root_documents': [rdoc],
                       'state': 'PENDING',
                       'result': None,
                       'task': (group, fun, kwargs),
                    }
                    for parent in parents:
                        result_data[parent]['children'].append(task_id)
                    task = self.celery.app.tasks[u'nidaba.{}.{}'.format(group, fun)]
                    if sequential:
                        r[-1].append(task.s(batch_id=self.id, task_id=task_id, **kwargs))
                    else:
                        r.append(task.s(batch_id=self.id, task_id=task_id, **kwargs))
            prev = nprev
            t = self.celery.app.tasks[u'nidaba.util.barrier'].s(merging=mmode, sequential=sequential, replace=r, root_docs=self.docs)
            first.append(t)
        with self.redis.pipeline() as pipe:
            while(1):
                try:
                    pipe.watch(self.id)
                    self._restore_and_create_scratchpad(pipe)
                    # also deletes the scratchpad 
                    pipe.set(self.id, json.dumps(result_data))
                    pipe.execute()
                    break
                except self.redis.WatchError:
                    continue
        chain(first).apply_async(args=[self.docs])
        return self.id

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
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        r = requests.get('{}/batch/{}'.format(self.host, self.id))
        r.raise_for_status()
        batch = r.json()
        if 'scratchpad' in batch:
            return u'NONE'
        elif 'chains' in batch:
            self.lock = True
            batch = batch['chains']
            st = u'SUCCESS'
            for subtask in batch.itervalues():
                if subtask['state'] == 'PENDING' or subtask['state'] == 'RUNNING':
                    st = u'PENDING'
                if subtask['state'] == 'FAILURE':
                    return u'FAILURE'
            return st
        else:
            return u'NONE'

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

    def get_results(self):
        """
        Retrieves the storage tuples of a successful batch.

        Returns:
        """
        if not self.id:
            raise NidabaInputException('Object not attached to batch.')
        r = requests.get('{}/batch/{}'.format(self.host, self.id))
        r.raise_for_status()
        if 'chains' in r.json():
            self.lock = True
            batch = r.json()['chains']
            outfiles = []
            for subtask in batch.itervalues():
                if len(subtask['children']) == 0 and not subtask['housekeeping'] and subtask['result'] is not None:
                    outfiles.append((subtask['result'], subtask['root_document']))
            return outfiles
        else:
            return None

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
        """
        Add a document to the batch.

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
        r = requests.post('{}/batch/{}/tasks/{}/{}'.format(self.host, self.id,
                                                           group, method),
                          json=kwargs)  
        r.raise_for_status()

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
