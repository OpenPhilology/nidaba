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
import json

from flask import Flask, render_template, request
from flask import Response, url_for, jsonify, send_file

from nidaba import storage
from nidaba import celery
from nidaba.nidaba import SimpleBatch

log = logging.getLogger('nidaba')

nidaba = Flask('nidaba')


def get_flask():
    return nidaba


@nidaba.errorhandler(404)
def batch_not_found(error=None):
    message = {
        'status': 404,
        'message': 'Batch Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


@nidaba.errorhandler(404)
def file_not_found(error=None):
    message = {
        'status': 404,
        'message': 'File Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


@nidaba.errorhandler(404)
def task_not_found(error=None):
    message = {
        'status': 404,
        'message': 'Task Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


@nidaba.route('/')
@nidaba.route('/index')
def indexRoute():
    log.debug('routing to the index')
    return render_template("index.html")


@nidaba.route('/batch', methods=['POST'])
def batchRoute():
    jobid = unicode(uuid.uuid4())
    log.debug('routing to batch with POST: {}'.format(jobid))
    storage.prepare_filestore(jobid)
    SimpleBatch(jobid)
    data = {'id': jobid,
            'url': url_for('specificBatchRoute', specificBatch=jobid)}
    resp = jsonify(data)
    resp.status_code = 201
    return resp


@nidaba.route('/batch/<specificBatch>', methods=['GET', 'POST'])
def specificBatchRoute(specificBatch):
    log.debug('routing to specific batch with URN: ' + str('%s' % specificBatch))
    try:
        batch = SimpleBatch(specificBatch)
    except:
        return batch_not_found()

    if request.method == 'GET':
        if batch.is_running():
            resp = jsonify({'chains': batch.get_extended_state()})
        else:
            docs = []
            for doc in batch.docs:
                docs.append({'name': doc[1],
                             'url': url_for('pagesRoute', batch=doc[0],
                                            file=doc[1])})

            jsonify({'pages': docs,
                     'tasks': batch.tasks})
            resp = jsonify({})
        resp.status_code = 200
    elif request.method == 'POST':
        if batch.get_state() == 'NONE':
            try:
                batch.run()
                resp = jsonify({'id': specificBatch,
                                'url': url_for('specificBatchRoute',
                                               specificBatch=specificBatch)})
                resp.status_code = 202
                return resp
            except:
                resp = jsonify({'message': 'Batch could not be executed'})
                resp.status_code = 400
                return resp
        else:
            resp = jsonify({'message': 'Batch already executed.'})
            resp.status_code = 409
            return resp
    return resp


@nidaba.route('/batch/<specificBatch>/pages', methods=['GET', 'POST'])
def batchPagesRoute(specificBatch):
    log.debug('routing to images of batch with URN: {}'.format(specificBatch))
    try:
        batch = SimpleBatch(specificBatch)
    except:
        return batch_not_found()

    if request.method == 'GET':
        data = []
        for doc in batch.docs:
            data.append({'name': doc[1],
                         'url': url_for('pagesRoute', batch=doc[0],
                                        file=doc[1])})
        resp = Response(json.dumps(data), status=200,
                        mimetype='application/json')
    elif request.method == 'POST':
        data = []
        for file in request.files.getlist('scans'):
            with storage.StorageFile(specificBatch, file.filename, 'wb') as fp:
                file.save(fp)
                file.close()
                batch.add_document(fp.storage_path)
            data.append({'name': file.filename,
                         'url': url_for('pagesRoute', batch=specificBatch,
                                        file=file.filename)})
        resp = Response(json.dumps(data), status=201,
                        mimetype='application/json')
    return resp


@nidaba.route('/batch/<specificBatch>/tasks', methods=['GET'])
def batchTasksRoute(specificBatch):
    log.debug('routing to images of batch with URN: {}'.format(specificBatch))
    try:
        batch = SimpleBatch(specificBatch)
    except:
        return batch_not_found()

    tasks = batch.get_tasks()
    resp = Response(json.dumps(tasks), status=200,
                    mimetype='application/json')
    return resp


@nidaba.route('/batch/<specificBatch>/tasks/<group>', methods=['GET'])
def batchTasksGroupRoute(specificBatch, group):
    log.debug('routing to tasks of batch with URN: {}'.format(specificBatch))
    try:
        batch = SimpleBatch(specificBatch)
    except:
        return batch_not_found()

    resp = Response(json.dumps(batch.tasks[group]), status=200,
                    mimetype='application/json')
    return resp


@nidaba.route('/batch/<specificBatch>/tasks/<group>/<task>', methods=['GET', 'POST'])
def batchTasksGroupTaskRoute(specificBatch, group, task):
    log.debug('routing to images of batch with URN: {}'.format(specificBatch))
    try:
        batch = SimpleBatch(specificBatch)
    except:
        return batch_not_found()

    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        if request.json is None:
            kwargs = {}
        else:
            kwargs = request.json
        try:
            batch.add_task(group, task, **kwargs)
        except Exception as e:
            resp = jsonify({'message': str(e)})
            resp.status_code = 400
            return resp
        resp = Response(status=201, mimetype='application/json')
    return resp


@nidaba.route('/pages/<batch>/<path:file>', methods=['GET'])
def pagesRoute(batch, file):
    log.debug('routing to pages with URN: {}/{}'.format(batch, file))

    try:
        fp = storage.StorageFile(batch, file, 'rb')
    except:
        return file_not_found()

    return send_file(fp)


@nidaba.route('/tasks', methods=['GET'])
def tasksRoute():
    log.debug('routing to tasks')
    groups = set(task.split('.')[1] for task in celery.app.tasks.iterkeys() if
                 task.startswith('nidaba'))
    data = [{'name': group, 'url': url_for('tasksGroupRoute', group=group)} for
            group in groups]
    resp = Response(json.dumps(data), status=200,
                    mimetype='application/json')
    return resp


@nidaba.route('/tasks/<group>', methods=['GET'])
def tasksGroupRoute(group):
    log.debug('Routing to tasks with group {}'.format(group))
    data = []
    for id, task in celery.app.tasks.iteritems():
        try:
            pre, g, t = id.split('.')
        except ValueError:
            continue
        if pre != 'nidaba' or group != g:
            continue
        else:
            data.append({'name': t, 'url': url_for('tasksGroupTaskRoute',
                                                   group=group, task=t)})
    resp = Response(json.dumps(data), status=200,
                    mimetype='application/json')
    return resp


@nidaba.route('/tasks/<group>/<task>', methods=['GET'])
def tasksGroupTaskRoute(group, task):
    log.debug('Routing to tasks with group {}, task {}'.format(group, task))
    data = []
    full_task = 'nidaba.{}.{}'.format(group, task)
    if full_task not in celery.app.tasks:
        return task_not_found()

    data = {'name': task,
            'group': group,
            'args': celery.app.tasks[full_task].get_valid_args()}
    resp = Response(json.dumps(data), status=200,
                    mimetype='application/json')
    return resp
