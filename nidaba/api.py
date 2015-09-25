# -*- coding: utf-8 -*-
"""
nidaba.api
~~~~~~~~~~

Exposes the functionality of the ``SimpleBatch`` class using a restful
interface.

For a documentation of the interface see the :ref:`API docs <api>`.
"""

from __future__ import unicode_literals, print_function, absolute_import

import logging
import uuid
import werkzeug
import json

from flask import Flask, request
from flask import send_file
from flask_restful import abort, Api, Resource, url_for, reqparse

from nidaba import storage
from nidaba import celery
from nidaba.nidaba import SimpleBatch
from nidaba.nidabaexceptions import NidabaStorageViolationException

log = logging.getLogger(__name__)
log.propagate = False
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(process)d] [%(levelname)s] %(message)s', 
                              datefmt='[%Y-%m-%d %H:%M:%S %z]')
ch.setFormatter(formatter)
log.addHandler(ch)

nidaba = Flask('nidaba')
api = Api(nidaba)

def get_flask():
    return nidaba

@api.resource('/pages/<batch>/<path:file>', methods=['GET'])
class Page(Resource):

    def get(self, batch, path):
        log.debug('routing to pages with URN: {}/{}'.format(batch, file))
        try:
            fp = storage.StorageFile(batch, file, 'rb')
        except:
            log.debug('File {} not found in {}'.format(file, batch))
            return {'message': 'File not found'}, 404
        return send_file(fp)

@api.resource('/tasks', '/tasks/<group>', '/tasks/<group>/<task>')
class Task(Resource):

    def get(self, group=None, task=None):
        log.debug('Routing to tasks with group {}, method {}'.format(group, task))
        tasks = SimpleBatch.get_available_tasks()
        if group and group not in tasks:
            return {'message': 'Unknown group {}'.format(group)}, 404
        elif task and task not in tasks[group]:
            return {'message': 'Unknown task {}'.format(task)}, 404
        if group:
            tasks = {group: tasks[group]}
        if task:
            tasks = {group: {task: tasks[group][task]}}
        return tasks, 200


@api.resource('/batch/<string:batch_id>')
class Batch(Resource):

    def get(self, batch_id):
        log.debug('Routing to batch {} (GET)'.format(batch_id))
        res = {}
        try:
            batch = SimpleBatch(batch_id)
        except:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        res['pages'] = url_for('batchpages', batch_id=batch_id)
        res['tasks'] = url_for('batchtasks', batch_id=batch_id)
        if batch.is_running():
            res['chains'] = batch.get_extended_state()
        return res, 200

    def post(self, batch_id):
        log.debug('Routing to batch {} (POST)'.format(batch_id))
        try:
            batch = SimpleBatch(batch_id)
        except:
            log.debug('Batch {} not found'.format(batch_id))
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        if batch.get_state() == 'NONE':
            try:
                batch.run()
                return {'id': batch_id, 'url': url_for('batch', batch_id=batch_id)}, 202
            except:
                log.debug('Batch {} could not be executed'.format(batch_id))
                return {'message': 'Batch could not be executed'}, 400
        else:
            log.debug('Batch {} already executed'.format(batch_id))
            return {'message': 'Batch already executed'}, 409


@api.resource('/batch')
class BatchCreator(Resource):

    def post(self):
        log.debug('Routing to batch with POST')
        batch = SimpleBatch()
        data = {'id': batch.id, 'url': url_for('batch', batch_id=batch.id)}
        log.debug('Created batch {}'.format(batch.id))
        return data, 201

@api.resource('/batch/<string:batch_id>/tasks',
              '/batch/<string:batch_id>/tasks/<group>',
              '/batch/<string:batch_id>/tasks/<group>/<task>')
class BatchTasks(Resource):

    def get(self, batch_id, group=None, task=None):
        log.debug('Routing to task {}.{} of {} (GET)'.format(group, task, batch_id))
        try:
            batch = SimpleBatch(batch_id)
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
        log.debug('Routing to task {}.{} of {} (POST)'.format(group, task, batch_id))
        try:
            batch = SimpleBatch(batch_id)
        except:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        try:
            batch.add_task(group, task, **request.form.to_dict(flat=True))
        except Exception as e:
            log.debug('Adding task {} to {} failed: {}'.format(task, specificBatch, str(e)))
            return {'message': str(e)}, 400


@api.resource('/batch/<string:batch_id>/pages')
class BatchPages(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('auxiliary', type=bool, default=False, location='args', 
                        help='Files not added as batch input but accessible for '
                        'other purposes')
    parser.add_argument('scans', type=werkzeug.datastructures.FileStorage,
                        location='files', action='append', required=True)

    def get(self, batch_id):
        log.debug('Routing to pages of {} (GET)'.format(batch_id))
        try:
            batch = SimpleBatch(batch_id)
        except:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        data = []
        for doc in batch.get_documents():
            data.append({'name': doc[1],
                         'url': url_for('page', batch=doc[0], file=doc[1])})
        return data, 200

    def post(self, batch_id):
        args = self.parser.parse_args()
        log.debug('Routing to pages {} of {} (POST)'.format(
                    [x.filename for x in args['scans']], batch_id))
        try:
            batch = SimpleBatch(batch_id)
        except:
            return {'message': 'Batch Not Found: {}'.format(batch_id)}, 404
        data = []
        for file in args['scans']:
            try:
                fp = storage.StorageFile(batch_id, file.filename, 'wb')
            except NidabaStorageViolationException as e:
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
                         'url': url_for('page', batch=batch_id, file=file.filename)})
        return data, 201
