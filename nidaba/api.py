# -*- coding: utf-8 -*-
"""
nidaba.api
~~~~~~~~~~

Exposes the functionality of the ``Batch`` class using a restful
interface.

For a documentation of the interface see the :ref:`API docs <api>`.
"""

from __future__ import unicode_literals, print_function, absolute_import

import logging
import uuid
import werkzeug
import json
import mimetypes

from flask import Flask, Blueprint, request
from flask import send_file
from flask_restful import abort, Api, Resource, url_for, reqparse

from nidaba import storage
from nidaba.nidaba import Batch as nBatch
from nidaba.nidabaexceptions import NidabaStorageViolationException


log = logging.getLogger(__name__)
log.propagate = False
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(process)d] [%(levelname)s] %(message)s', 
                              datefmt='[%Y-%m-%d %H:%M:%S %z]')
ch.setFormatter(formatter)
log.addHandler(ch)

api_v1 = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(api_v1)

def get_blueprint():
    return api_v1

# helper so autodoc finds endpoints
def create_app():
    app = Flask('nidaba')
    app.register_blueprint(get_blueprint())
    return app

@api.resource('/pages/<batch>/<path:file>', methods=['GET'])
class Page(Resource):

    def get(self, batch, file):
        """
        Retrieves the file at *file* in batch *batch*.
    
        ** Request **
    
        .. sourcecode:: http
    
            GET /pages/:batch/:path
    
        ** Response **
    
        .. sourcecode:: http
    
            HTTP/1.1 200 OK
            Content-Type: application/octet-stream
    
            ...
    
        :param batch: batch's unique id
        :type batch: str
        :param file: path to the batch's file
        :type file: path
        :status 200: No error
        :status 404: File not found
        """
        log.debug('routing to pages with URN: {}/{}'.format(batch, file))
        try:
            fp = storage.StorageFile(batch, file, 'rb')
        except:
            log.debug('File {} not found in {}'.format(file, batch))
            return {'message': 'File not found'}, 404
        return send_file(fp, mimetype=mimetypes.guess_type(file)[0])

@api.resource('/tasks', '/tasks/<group>', '/tasks/<group>/<task>')
class Task(Resource):
    def get(self, group=None, task=None):
        """
        Retrieves the list of available tasks, their arguments and valid values
        for those arguments.

        ** Request **
    
        .. sourcecode:: http
    
            GET /tasks
    
        ** Response **
    
        .. sourcecode:: http
    
            HTTP/1.1 200 OK

            {
                "img": {
                    "deskew": {}, 
                    "dewarp": {}, 
                    "rgb_to_gray": {}
                },
                "binarize": {
                    "nlbin": {
                        "border": "float", 
                        "escale": "float", 
                        "high": [
                            0, 
                            100
                        ], 
                        "low": [
                            0, 
                            100
                        ], 
                    }, 
                    "otsu": {}, 
                    "sauvola": {
                        "factor": [
                            0.0, 
                            1.0
                        ], 
                        "whsize": "int"
                    }
                },
                "segmentation": {
                    "kraken": {}, 
                    "tesseract": {}
                },
                "ocr": {
                    "kraken": {
                        "model": [
                            "fraktur.pyrnn.gz", 
                            "default", 
                            "teubner"
                        ]
                    }, 
                    "tesseract": {
                        "extended": [
                            false, 
                            true
                        ], 
                        "languages": [
                            "chr", 
                            "chi_tra", 
                            "ita_old", 
                            "ceb", 
                        ]
                    }
                }, 
                "postprocessing": {
                    "spell_check": {
                        "filter_punctuation": [
                            true, 
                            false
                        ], 
                        "language": [
                            "latin", 
                            "polytonic_greek"
                        ]
                    }
                },
                "output": {
                    "metadata": {
                        "metadata": "file", 
                        "validate": [
                            true, 
                            false
                        ]
                    }, 
                    "tei2hocr": {}, 
                    "tei2simplexml": {}, 
                    "tei2txt": {}
                }
            }

        It is also possible to retrieve only a subset of task definitions by
        adding to the request a task group and/or the task name:

        ** Request **

        .. sourcecode:: http
    
            GET /tasks/segmentation

        ** Response **

        .. sourcecode:: http

            HTTP/1.1 200 OK
            
            {
                "segmentation": {
                    "kraken": {}, 
                    "tesseract": {}
                }
            }

        Currently there are 4 different argument types:

            * "int": An integer
            * "float": A float (floats serialized to integers, i.e. 1.0 to 1
                       are also accepted)
            * "str": An UTF-8 encoded string
            * "file": A file on the storage medium, referenced by its URL

        Finally there are lists of valid argument values where one or more
        values out of the list may be picked and value ranges
        """
        log.debug('Routing to tasks with group {}, method {}'.format(group, task))
        tasks = nBatch().get_available_tasks()
        if group and group not in tasks:
            return {'message': 'Unknown group {}'.format(group)}, 404
        elif task and task not in tasks[group]:
            return {'message': 'Unknown task {}'.format(task)}, 404
        if group:
            tasks = {group: tasks[group]}
        if task:
            tasks = {group: {task: tasks[group][task]}}
        return tasks, 200


@api.resource('/batch/<batch_id>')
class Batch(Resource):

    def get(self, batch_id):
        """
        Retrieves the state of batch *batch_id*.
    
        ** Request **
    
        .. sourcecode:: http
    
            GET /batch/:batch_id
    
        ** Response **
    
        .. sourcecode:: http
    
            HTTP/1.1 200 OK

        :param batch_id: batch identifier
        :type batch_id: string
        :status 200: No error
        :status 404: No such batch
        """
        log.debug('Routing to batch {} (GET)'.format(batch_id))
        res = {}
        try:
            batch = nBatch(batch_id)
        except NidabaInputException:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        except:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        res['pages'] = url_for('api.batchpages', batch_id=batch_id)
        res['tasks'] = url_for('api.batchtasks', batch_id=batch_id)
        if batch.is_running():
            res['chains'] = batch.get_extended_state()
            # replace all document tuples with URLs to the page resource
            def replace_docs(state):
                for k in state.keys():
                    if k in ['root_documents', 'result', 'doc']:
                        if state[k] is not None and isinstance(state[k][0], list):
                            docs = []
                            for doc in state[k]:
                                docs.append(url_for('api.page', batch=doc[0], file=doc[1]))
                            state[k] = docs
                        elif state[k] is not None:
                            state[k] = url_for('api.page', batch=state[k][0], file=state[k][1])
                    if isinstance(state[k], dict):
                        replace_docs(state[k])
            replace_docs(res['chains'])
        return res, 200

    def post(self, batch_id):
        """
        Executes batch with identifier *batch_id*
    
        ** Request **
    
        .. sourcecode:: http
    
            POST /batch/:batch_id
    
        ** Response **
    
        .. sourcecode:: http
    
            HTTP/1.1 202 ACCEPTED
   
        :param batch_id: batch's unique id
        :type batch_id: string 
        :status 202: Successfully executed
        :status 400: Batch could not be executed
        :status 404: No such batch
        :status 409: Trying to reexecute an already executed batch
        """
        log.debug('Routing to batch {} (POST)'.format(batch_id))
        try:
            batch = nBatch(batch_id)
        except:
            log.debug('Batch {} not found'.format(batch_id))
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        if batch.get_state() == 'NONE':
            try:
                batch.run()
                return {'id': batch_id, 'url': url_for('api.batch', batch_id=batch_id)}, 202
            except:
                log.debug('Batch {} could not be executed'.format(batch_id), exc_info=True)
                return {'message': 'Batch could not be executed'}, 400
        else:
            log.debug('Batch {} already executed'.format(batch_id))
            return {'message': 'Batch already executed'}, 409


@api.resource('/batch')
class BatchCreator(Resource):

    def post(self):
        """
        Creates a new batch and returns it identifier.

        ** Request **
    
        .. sourcecode:: http
    
            POST /batch
    
        ** Response **
    
        .. sourcecode:: http
    
            HTTP/1.1 201 CREATED

            {
                "id": "78a1f1e4-cc76-40ce-8a98-77b54362a00e", 
                "url": "/batch/78a1f1e4-cc76-40ce-8a98-77b54362a00e"
            }
    
        :status 201: Successfully created
        """
        log.debug('Routing to batch with POST')
        batch = nBatch()
        data = {'id': batch.id, 'url': url_for('api.batch', batch_id=batch.id)}
        log.debug('Created batch {}'.format(batch.id))
        return data, 201

@api.resource('/batch/<batch_id>/tasks',
              '/batch/<batch_id>/tasks/<group>',
              '/batch/<batch_id>/tasks/<group>/<task>')
class BatchTasks(Resource):

    def get(self, batch_id, group=None, task=None):
        """
        Retrieves the list of tasks and their argument values associated with a
        batch, optionally limited to a specific group.

        ** Request **
    
        .. sourcecode:: http

            GET /batch/:batch_id/tasks    
    
        ** Response **
    
        .. sourcecode:: http
    
            HTTP/1.1 200 OK
            
            {
                "segmentation": [
                    ["tesseract", {}]
                ],
                "ocr": [
                    ["kraken", 
                        {
                            "model": "teubner", 
                        }
                    ]
                ]
            }


        To limit output to a specific group of tasks, e.g. segmentation or
        binarization append the group to the URL:

        ** Request **

        .. sourcecode:: http

            GET /batch/:batch_id/tasks/:group

        ** Response **

        .. sourcecode:: http

            HTTP/1.1 200 OK

            {
                'group': [
                    ["tesseract", {}],
                    ["kraken", {}]
                ]
            }

        :status 200: success
        :status 404: batch, group, or task not found.
        """
        log.debug('Routing to task {}.{} of {} (GET)'.format(group, task, batch_id))
        try:
            batch = nBatch(batch_id)
        except:
            log.debug('Batch {} not found'.format(batch_id))
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        tasks = batch.get_tasks()
        if group and group not in tasks:
            log.debug('Unknown group {} ({})'.format(group, batch_id))
            return {'message': 'Unknown group {}'.format(group)}, 404
        elif task and task not in tasks[group]:
            log.debug('Unknown task {}.{} ({})'.format(group, task, batch_id))
            return {'message': 'Unknown task {}'.format(task)}, 404
        if group:
            tasks = {group: tasks[group]}
        if task:
            tasks = {group: {task: tasks[group][task]}}
        return tasks, 200

    def post(self, batch_id, group=None, task=None):
        """
        Adds a particular configuration of a task to the batch identified by
        *batch_id*.

        ** Request **

            POST /batch/:batch_id/:group/:task

            {
                kwarg_1: "value",
                kwarg_2: 10,
                kwarg_3: 'true',
                kwarg_4: ["a", "b"],
                kwarg_5: '/pages/:batch_id/path'
            }

        ** Response **

        .. sourcecode:: http

            HTTP/1.1 201 CREATED

        To post files as arguments use their URL returned by the call that
        created them on the batch. Booleans are strings containing either the
        values 'True'/'true' or 'False'/'false'.

        :status 201: task created
        :status 404: batch, group, or task not found.
        """
        log.debug('Routing to task {}.{} of {} (POST)'.format(group, task, batch_id))
        try:
            batch = nBatch(batch_id)
        except:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        try:
            def arg_conversion(s):
                # JSON does not support booleans
                if s in ['True', 'true']:
                    return True
                elif s in ['False', 'false']:
                    return False
                # XXX: find a nicer way to rewrite page URLs
                base_url = url_for('api.page', batch=batch_id, file='')
                if isinstance(s, basestring) and s.startswith(base_url):
                    rem = s.replace(base_url, '', 1)
                    return (batch_id, rem)
                return s
            kwargs = {k: arg_conversion(v) for k, v in request.get_json().iteritems()}
            batch.add_task(group, task, **kwargs)
        except Exception as e:
            log.debug('Adding task {} to {} failed: {}'.format(task, batch_id, str(e)))
            return {'message': str(e)}, 422
        return {}, 201


@api.resource('/batch/<batch_id>/pages')
class BatchPages(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('auxiliary', type=bool, default=False, location='args', 
                        help='Files not added as batch input but accessible for '
                        'other purposes')
    parser.add_argument('scans', type=werkzeug.datastructures.FileStorage,
                        location='files', action='append', required=True)

    def get(self, batch_id):
        """
        Returns the list of pages associated with the batch with *batch_id*.

        ** Request **
    
        .. sourcecode:: http
    
            GET /batch/:batch/pages
    
        ** Response **
    
        .. sourcecode:: http
    
            HTTP/1.1 200 OK

            [
                {
                    "name": "0033.tif", 
                    "url": "/pages/63ca3ec7-2592-4c7d-9009-913aac42535d/0033.tif"
                }, 
                {
                    "name": "0072.tif", 
                    "url": "/pages/63ca3ec7-2592-4c7d-9009-913aac42535d/0072.tif"
                }, 
                {
                    "name": "0014.tif", 
                    "url": "/pages/63ca3ec7-2592-4c7d-9009-913aac42535d/0014.tif"
                }
            ]

        :status 200: success
        :status 404: batch not found
        """
        log.debug('Routing to pages of {} (GET)'.format(batch_id))
        try:
            batch = nBatch(batch_id)
        except:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        data = []
        for doc in batch.get_documents():
            data.append({'name': doc[1],
                         'url': url_for('api.page', batch=doc[0], file=doc[1])})
        return data, 200

    def post(self, batch_id):
        """
        Adds a page (really any type of file) to the batch identified by
        *batch_id*.

        ** Request **

            POST /batch/:batch/pages

        ** Response **

            HTTP/1.1 201 OK
            
            [
                {
                    "name": "0033.tif", 
                    "url": "/pages/63ca3ec7-2592-4c7d-9009-913aac42535d/0033.tif"
                }
            ]

        :form scans: file(s) to add to the batch

        :status 201: task created
        :status 403: file couldn't be created
        :status 404: batch not found
        """
        args = self.parser.parse_args()
        log.debug('Routing to pages {} of {} (POST)'.format(
                    [x.filename for x in args['scans']], batch_id))
        try:
            batch = nBatch(batch_id)
        except:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        data = []
        for file in args['scans']:
            try:
                fp = storage.StorageFile(batch_id, file.filename, 'wb')
            except NidabaStorageViolationException as e:
                log.debug('Failed to write file {}'.format(file.filename),
                          exc_info=True)
                return {'message': str(e)}, 403
            else:
                with fp:
                    file.save(fp)
                    file.close()
                    if args['auxiliary'] is False:
                        log.debug('Adding {}/{} to {}'.format(fp.storage_path[0], 
                                                              fp.storage_path[1],
                                                              batch_id))
                        batch.add_document(fp.storage_path)
            data.append({'name': file.filename,
                         'url': url_for('api.page', batch=batch_id, file=file.filename)})
        return data, 201
