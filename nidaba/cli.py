# -*- coding: utf-8 -*-
"""
This module encapsulates all shell callable functions of nidaba.
"""

from __future__ import absolute_import, print_function

from signal import signal, SIGPIPE, SIG_DFL
from inspect import getcallargs, getdoc
from itertools import cycle
from pprint import pprint
from glob import glob

from nidaba.nidaba import NetworkSimpleBatch, Batch
from nidaba.nidabaexceptions import NidabaInputException

import uuid
import shutil
import os.path
import sys
import click

# ignore SIGPIPE
signal(SIGPIPE,SIG_DFL) 

spinner = cycle([u'⣾', u'⣽', u'⣻', u'⢿', u'⡿', u'⣟', u'⣯', u'⣷'])

def spin(msg):
    click.echo(u'\r\033[?25l{}\t\t{}'.format(msg, next(spinner)), nl=False)


@click.group()
@click.version_option()
def client_only():
    """
    API-only version of the nidaba client
    """

@click.group()
@click.version_option()
def main():
    """
    Sends jobs to nidaba and retrieves their status.
    """


def conv_arg_string(s):
    """
    A small helper function intended to coerce an input string to types in the
    order int -> float -> bool -> unicode -> input. Also resolves lists of
    these values.

    Args:
        s (unicode):

    Returns:
        int or float or unicode or original input type: Input variable coerced
        to the highest data type in the ordering.
    """
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            if s in ['True', 'true']:
                return True
            elif s in ['False', 'false']:
                return False
            try:
                if s[0] == '[' and s[-1] == ']':
                    return [conv_arg_string(x) for x in s[1:-1].split(',')]
                return unicode(s)
            except UnicodeDecodeError:
                return s


def help_tasks(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    from nidaba import celery
    t = celery.app.tasks
    hidden = ['util']
    last = u''
    docs = u''
    for k in sorted(t.keys()):
        hier = k.split('.')
        if hier[0] == 'nidaba':
            if hier[1] in hidden:
                continue
            elif hier[1] != last:
                docs += '{}\n{}\n\n'.format(hier[1].title(), len(hier[1]) *
                                            '-')
                last = hier[1]
            docs += '{}\n{}\n\n{}'.format(hier[-1], len(hier[-1]) * '~',
                                          getdoc(t[k].run).decode('utf-8').partition('Returns:')[0])
    click.echo_via_pager(docs)
    ctx.exit()


def validate_definition(ctx, param, value):
    """
    Validates all task definitions of a group and returns them as a list.
    """
    definitions = []
    for alg in value:
        (task, _, params) = alg.partition(u':')
        configurations = []
        for conf in params.split(u';'):
            kwargs = {}
            vals = conf.split(u'=')
            key = None
            for args in vals:
                head, sep, tail = args.rpartition(',')
                if head:
                    kwargs[key] = conv_arg_string(head)
                elif not sep and key:
                    kwargs[key] = conv_arg_string(tail)
                if tail:
                    key = tail
            configurations.append(kwargs)
        definitions.append([task, configurations])
    return definitions


def move_to_storage(batch, kwargs):
    """
    Takes as dictionary of kwargs and moves the suffix of all keys starting
    with the string 'file:' to the storage medium, prepending a unique
    identifier. The path components are rewritten in storage tuple form and the
    modified dictionary is returned.

    It is assumed that the filestore is already created.
    """

    nkwargs = {}
    def do_move(batch, src):
        if isinstance(batch, NetworkSimpleBatch):
            dst = os.path.basename(src)
            def callback(monitor):
                spin(u'Uploading {}'.format(dst))
            batch.add_document(src, callback, auxiliary=True)
            click.secho(u'\b\u2713', fg='green', nl=False)
            click.echo('\033[?25h\n', nl=False)
        else:
            from nidaba import storage
            suffix = uuid.uuid4()
            dst = os.path.basename(src) + '_' + unicode(suffix)
            shutil.copy2(src, storage.get_abs_path(batch.id, dst))
        return (batch.id, dst)
    for k, v in kwargs.iteritems():
        if isinstance(v, basestring) and v.startswith('file:'):
            v = v.replace('file:', '', 1)
            # unglobulate input files
            nkwargs[k] = [do_move(batch, f) for f in glob(v)]
            if len(nkwargs[k]) == 1:
                nkwargs[k] = nkwargs[k][0]
        else:
            nkwargs[k] = v
    return nkwargs


@main.command()
@click.option('-h', '--host', default=None, 
              help='Address of the API service. If none is given a local '
              'installation of nidaba will be invoked.')
@click.option('--preprocessing', '-i', multiple=True,
              callback=validate_definition, help='a configuration for a single'
              'image preprocessing algorithm in the format '
              'algorithm:param1,param2;param1,param2;...')
@click.option('--binarize', '-b', multiple=True, callback=validate_definition,
              help='a configuration for a single binarization algorithm in '
              'the format algorithm:param1,param2;param1,param2;...')
@click.option('--segmentation', '-l', multiple=True,
              callback=validate_definition,
              help='A configuration for a single page segmentation algorithm in '
              'the format algorithm:param1,param2;param1,param2;...')
@click.option('--ocr', '-o', multiple=True, callback=validate_definition,
              help='A configuration for a single OCR engine in the format '
              'engine:param1,param2;param1,param2;...')
@click.option('--stats', '-s', multiple=True, callback=validate_definition,
              help='A configuration for a single post-OCR measure in the '
              'format measure:param1,param2;param1;param2...')
@click.option('--postprocessing', '-p', multiple=True,
              callback=validate_definition, help='A configuration for a '
              'single postprocessing task in the format '
              'task:param1,param2;param1;param1...')
@click.option('--output', '-f', multiple=True,
              callback=validate_definition, help='A configuration for a '
              'single output layer transformation in the format'
              'task:param1,param2;param1;param1...')
@click.option('--archive', '-a', multiple=True,
              callback=validate_definition, help='A configuration for a '
              'single archiving layer transformation in the format'
              'task:param1,param2;param1;param1...')
@click.option('--grayscale', default=False, help='Skip grayscale '
              'conversion using the ITU-R 601-2 luma transform if the input '
              'documents are already in grayscale.', is_flag=True)
@click.option('--help-tasks', is_eager=True, is_flag=True, callback=help_tasks,
              help='Accesses the documentation of all tasks contained in '
              'nidaba itself and in configured plugins.')
@click.argument('files', type=click.Path(exists=True), nargs=-1, required=True)
def batch(files, host, preprocessing, binarize, ocr, segmentation, stats,
          postprocessing, output, archive, grayscale, help_tasks):
    """
    Add a new job to the pipeline.
    """
   
    if host:
        batch = NetworkSimpleBatch(host)
        click.echo(u'Preparing filestore\t\t[', nl=False)
        try:
            batch.create_batch()
        except:
            click.secho(u'\u2717', fg='red', nl=False)
            click.echo(']')
            exit()
        click.secho(u'\u2713', fg='green', nl=False)
        click.echo(']')
        for doc in files:
            def callback(monitor):
                spin(u'Uploading {}'.format(doc))
            batch.add_document(doc, callback)
            click.secho(u'\b\u2713', fg='green', nl=False)
            click.echo('\033[?25h\n', nl=False)
    else:
        from nidaba import storage
        click.echo(u'Preparing filestore\t\t[', nl=False)
        try:
            batch = Batch()
        except:
            raise
            click.secho(u'\u2717', fg='red', nl=False)
            click.echo(']')
            exit()
        for doc in files:
            shutil.copy2(doc, storage.get_abs_path(batch.id, os.path.basename(doc)))
            batch.add_document((batch.id, os.path.basename(doc)))
        click.secho(u'\u2713', fg='green', nl=False)
        click.echo(']')
    click.echo(u'Building batch\t\t\t[', nl=False)
    if not grayscale:
        batch.add_task('img', 'rgb_to_gray')
    if preprocessing:
        for alg in preprocessing:
            for kwargs in alg[1]:
                kwargs = move_to_storage(batch, kwargs)
                batch.add_task('img', alg[0], **kwargs)
    if binarize:
        for alg in binarize:
            for kwargs in alg[1]:
                kwargs = move_to_storage(batch, kwargs)
                batch.add_task('binarize', alg[0], **kwargs)
    if segmentation:
        for alg in segmentation:
            for kwargs in alg[1]:
                kwargs = move_to_storage(batch, kwargs)
                batch.add_task('segmentation', alg[0], **kwargs)
    if ocr:
        for alg in ocr:
            for kwargs in alg[1]:
                kwargs = move_to_storage(batch, kwargs)
                batch.add_task('ocr', alg[0], **kwargs)
    if stats:
        for alg in stats:
            for kwargs in alg[1]:
                kwargs = move_to_storage(batch, kwargs)
                batch.add_task('stats', alg[0], **kwargs)
    if postprocessing:
        for alg in postprocessing:
            for kwargs in alg[1]:
                kwargs = move_to_storage(batch, kwargs)
                batch.add_task('postprocessing', alg[0], **kwargs)
    if output:
        for alg in output:
            for kwargs in alg[1]:
                kwargs = move_to_storage(batch, kwargs)
                batch.add_task('output', alg[0], **kwargs)
    if archive:
        for alg in archive:
            for kwargs in alg[1]:
                kwargs = move_to_storage(batch, kwargs)
                batch.add_task('archive', alg[0], **kwargs)
    batch.run()
    click.secho(u'\u2713', fg='green', nl=False)
    click.echo(']')
    click.echo(batch.id)


@main.command()
def worker():
    """
    Starts a celery worker.
    """
    from nidaba import celery
    celery.app.worker_main(argv=sys.argv[:1])


@main.command()
@click.pass_context
@click.option('-b', '--bind', default='127.0.0.1:8080', 
              help='Address and port to bind the application worker to.')
@click.option('-w', '--workers', default=1, type=click.INT, 
              help='Number of request workers')
def api_server(ctx, **kwargs):
    """
    Starts the nidaba API server using gunicorn.
    """

    try:
        from nidaba import api
        from nidaba import web
    except IOError as e:
        if e.errno == 2:
            click.echo('No configuration file found at {}'.format(e.filename))
            ctx.exit()

    import logging
    import gunicorn.app.base

    from flask import Flask
    from gunicorn.six import iteritems

    logging.basicConfig(level=logging.DEBUG)

    app = Flask('nidaba')
    app.register_blueprint(api.get_blueprint())
    app.register_blueprint(web.get_blueprint())


    class APIServer(gunicorn.app.base.BaseApplication):

        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super(APIServer, self).__init__()

        def load_config(self):
            config = dict([(key, value) for key, value in iteritems(self.options)
                           if key in self.cfg.settings and value is not None])
            for key, value in iteritems(config):
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    APIServer(app, options=kwargs).run()


@main.command()
@click.pass_context
def config(ctx):
    """
    Displays the current configuration.
    """
    try:
        from nidaba.config import nidaba_cfg
    except IOError as e:
        if e.errno == 2:
            click.echo('No configuration file found at {}'.format(e.filename))
            ctx.exit()
    pprint(nidaba_cfg)


@main.command()
@click.pass_context
def plugins(ctx):
    """
    Displays available plugins and if they're enabled.
    """
    try:
        from nidaba.config import nidaba_cfg
    except IOError as e:
        if e.errno == 2:
            click.echo('plugins command only available for local installations.')
            ctx.exit()

    import stevedore

    mgr = stevedore.ExtensionManager(namespace='nidaba.plugins')
    enabled = set(nidaba_cfg['plugins_load'].keys()).intersection(set(mgr.names()))
    disabled = set(mgr.names()) - enabled
    for plugin in mgr.names():
        click.echo(plugin, nl=False)
        if plugin in disabled:
            click.secho(u' (disabled)', fg='red')
        else:
            click.secho(u' (enabled)', fg='green')


@main.command()
@click.option('-h', '--host', default=None, 
              help='Address of the API service. If none is given a local '
              'installation of nidaba will be invoked.')
@click.option('-v', '--verbose', count=True)
@click.argument('job_id', nargs=1)
def status(verbose, host, job_id):
    """
    Diplays the status and results of jobs.
    """
    click.secho('Status:', underline=True, nl=False)
    if host:
        batch = NetworkSimpleBatch(host, job_id)
    else:
        try:
            batch = Batch(job_id)
        except NidabaInputException:
            click.echo(' UNKNOWN')
            return

    state = batch.get_extended_state()
    if not state:
        click.echo(' UNKNOWN')
        return

    bs = 'success'
    done = 0
    running = 0
    pending = 0
    failed = 0
    results = []
    errors = []
    expected = len(state)
    failed_children = set()
    for task_id, subtask in state.iteritems():
        if subtask['state'] == 'SUCCESS':
            done += 1
        elif subtask['state'] == 'RUNNING':
            running += 1
            if bs == 'success':
                bs = 'pending'
        elif subtask['state'] == 'PENDING':
            pending += 1
            if bs == 'success':
                bs = 'pending'
        elif subtask['state'] == 'FAILURE':
            failed += 1
            children = []
            if not isinstance(subtask['children'], list):
                subtask['children'] = [subtask['children']]
            for child in subtask['children']:
                if not isinstance(state[child]['children'], list):
                    state[child]['children'] = [state[child]['children']]
                children.extend(state[child]['children'])
                failed_children.add(child)
            errors.append(subtask)
            bs = 'failed'

        if len(subtask['children']) == 0 and subtask['result'] is not None:
            # try to find statistics results
            parents = [task_id] + subtask['parents']
            misc = None
            for parent in parents:
                parents.extend(state[parent]['parents'])
                if 'misc' in state[parent]:
                    misc = state[parent]['misc']
                    break
            results.append((subtask['result'], subtask['root_documents'], misc))
    final = '(final)' if not expected - failed - done - len(failed_children) else ''
    click.echo(' {} {}\n'.format(bs, final))
    click.echo('{}/{} tasks completed. {} running.\n'.format(done, len(state), running))
    click.secho('Output files:\n', underline=True)
    results = sorted(results, key=lambda x: x[0][1])
    if results:
        for doc in results:
            if host:
                output = doc[0]
            else:
                from nidaba import storage
                output = click.format_filename(storage.get_abs_path(*doc[0]))
            if doc[2] is not None:
                click.echo(u'{} \u2192 {} ({:.1f}% / {})'.format(', '.join(x[1] for x in doc[1]),
                                                                 output,
                                                                 100 *
                                                                 doc[2]['edit_ratio'],
                                                                 doc[2]['ground_truth'][1]))
            else:
                click.echo(u'{} \u2192 {}'.format(', '.join(x[1] for x in doc[1]), output))
    if errors:
        click.secho('\nErrors:\n', underline=True)
        for task in errors:
            tb = ''
            args = ''
            if verbose > 0:
                tb = task['errors'][2]
            if verbose > 1:
                task['errors'][0].pop('method')
                args = ', ' + str(task['errors'][0])
            click.echo('{0} ({1}{2}): {3}{4}'.format(task['task'][0],
                                                     task['root_document'][1],
                                                     args,
                                                     tb,
                                                     task['errors'][1]))

client_only.add_command(status)
client_only.add_command(batch)
