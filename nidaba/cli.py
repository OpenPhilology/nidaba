# -*- coding: utf-8 -*-
"""
This module encapsulates all shell callable functions of nidaba.
"""

from __future__ import absolute_import, print_function

from inspect import getcallargs, getdoc
from gunicorn.six import iteritems
from pprint import pprint

from nidaba.nidaba import NetworkSimpleBatch, SimpleBatch

import uuid
import shutil
import os.path
import sys
import click
import stevedore
import logging
import gunicorn.app.base


@click.group(epilog='This nidaba may or may not have Super Cow Powers')
@click.version_option()
def main():
    """
    Sends jobs to nidaba and retrieves their status.
    """


def int_float_bool_or_str(s):
    """
    A small helper function intended to coerce an input string to types in the
    order int -> float -> bool -> unicode -> input.

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
            for arg in conf.split(u','):
                if '=' in arg:
                    k, v = arg.split('=')
                    kwargs[k] = int_float_bool_or_str(v)
                else:
                    raise click.BadParameter('Positional arguments are deprecated!')
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
    from nidaba import storage

    nkwargs = {}
    def do_move(batch, src):
        if isinstance(batch, NetworkSimpleBatch):
             batch.add_document(src, auxiliary=True)
             dst = os.path.basename(src)
        else:
            suffix = uuid.uuid4()
            dst = unicode(suffix) + '_' + os.path.basename(src)
            shutil.copy2(src, storage.get_abs_path(batch.id, dst))
        return (batch.id, dst)
    for k, v in kwargs.iteritems():
        if isinstance(v, basestring) and v.startswith('file:'):
            v = v.replace('file:', '', 1)
            nkwargs[k] = do_move(batch, v)
        else:
            nkwargs[k] = v
    return nkwargs


@main.command()
@click.option('-h', '--host', default=None, 
              help='Address of the API service. If none is given a local '
              'installation of nidaba will be invoked.')
@click.option('--binarize', '-b', multiple=True, callback=validate_definition,
              help='A configuration for a single binarization algorithm in '
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
# @click.option('--willitblend', 'blend',  default=False, help='Blend all '
#              'output files into a single hOCR document.', is_flag=True)
@click.option('--grayscale', default=False, help='Skip grayscale '
              'conversion using the ITU-R 601-2 luma transform if the input '
              'documents are already in grayscale.', is_flag=True)
@click.option('--help-tasks', is_eager=True, is_flag=True, callback=help_tasks,
              help='Accesses the documentation of all tasks contained in '
              'nidaba itself and in configured plugins.')
@click.argument('files', type=click.Path(exists=True), nargs=-1, required=True)
def batch(files, host, binarize, ocr, segmentation, stats, postprocessing, output,
          grayscale, help_tasks):
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
                click.echo(monitor.bytes_read)
            batch.add_document(doc, callback)
    else:
        from nidaba import storage
        click.echo(u'Preparing filestore\t\t[', nl=False)
        try:
            batch = SimpleBatch()
        except:
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
    if binarize:
        for alg in binarize:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task('binarize', alg[0], **kwargs)
    if segmentation:
        for alg in segmentation:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task('segmentation', alg[0], **kwargs)
    if ocr:
        for alg in ocr:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task('ocr', alg[0], **kwargs)
    if stats:
        for alg in stats:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task('stats', alg[0], **kwargs)
    if postprocessing:
        for alg in postprocessing:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task('postprocessing', alg[0], **kwargs)
    if output:
        for alg in output:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task('output', alg[0], **kwargs)
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
    except IOError as e:
        if e.errno == 2:
            click.echo('No configuration file found at {}'.format(e.filename))
            ctx.exit()

    logging.basicConfig(level=logging.DEBUG)

    api.get_flask()
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

    APIServer(api.get_flask(), options=kwargs).run()


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
@click.option('-v', '--verbose', count=True)
@click.option('-h', '--host', default=None, 
              help='Address of the API service. If none is given a local '
              'installation of nidaba will be invoked.')
@click.argument('job_id', nargs=1)
def status(verbose, host, job_id):
    """
    Diplays the status and results of jobs.
    """
    if host:
        batch = NetworkSimpleBatch(host, job_id)
    else:
        batch = SimpleBatch(job_id)

    state = batch.get_extended_state()

    click.secho('Status:', underline=True, nl=False)
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
    for subtask in state.itervalues():
        if subtask['state'] == 'SUCCESS':
            done += 1
        elif subtask['state'] == 'RUNNING':
            running += 1
        elif subtask['state'] == 'PENDING':
            pending += 1
            if bs == 'success':
                bs = 'pending'
        elif subtask['state'] == 'FAILURE':
            failed += 1
            errors.append(subtask)
            bs = 'failed'

        if len(subtask['children']) == 0 and not subtask['housekeeping'] and subtask['result'] is not None:
            results.append((subtask['result'], subtask['root_document']))

    click.echo(' {}\n'.format(bs))
    click.echo('{}/{} tasks completed. {} running.\n'.format(done, len(state), running))
    click.secho('Output files:\n', underline=True)
    if results and host:
        for doc in results:
            click.echo(doc[1] + u' \u2192 ' + doc[0])
    elif results:
        from nidaba import storage
        for doc in results:
            output = click.format_filename(storage.get_abs_path(*doc[0]))
            click.echo(doc[1][1] + u' \u2192 ' + output)
    if errors:
        click.secho('\nErrors:\n', underline=True)
        for task in errors:
            click.echo('{0} ({1}): {2}'.format(task['task'][0],
                                               task['root_document'][1],
                                               task['errors'][-1]))
