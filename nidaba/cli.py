#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module encapsulates all shell callable functions of nidaba.
"""

from __future__ import absolute_import, print_function, unicode_literals

from nidaba import Batch, storage
from nidaba.config import nidaba_cfg
from nidaba import celery
from pprint import pprint
from inspect import getcallargs, getdoc

import argparse
import re
import uuid
import shutil
import os.path
import sys
import click
import pkg_resources

@click.group(epilog='This nidaba may or may not have Super Cow Powers')
@click.version_option()
def main():
    """
    Sends jobs to nidaba and retrieves their status.
    """


def int_float_or_str(s):
    """
    A small helper function intended to coerce an input string to types in the
    order int -> float -> unicode -> input.

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
            try:
                return unicode(s)
            except UnicodeDecodeError:
                return s


def help_tasks(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
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
        task = param.human_readable_name + '.' + task
        if 'nidaba.' + task not in celery.app.tasks:
            raise click.BadParameter('Unknown task ' + task)
        configurations = []
        for conf in params.split(u';'):
            args = []
            kwargs = {}
            for arg in conf.split(u','):
                # treat as kwarg
                if '=' in arg:
                    k, v = arg.split('=')
                    kwargs[k] = int_float_or_str(v)
                # treat as arg as long as no kwargs were defined
                elif not kwargs and len(arg):
                    args.append(int_float_or_str(arg))
                elif not len(arg):
                    continue
                else:
                    raise click.BadParameter('Positional argument after '
                                             'keyword argument')
            try:
                fun = celery.app.tasks['nidaba.' + task]
                # fill in common kwargs (doc/method)
                args.insert(0, '')
                args.insert(0, '')
                kwargs = getcallargs(fun.run, *args, **kwargs)
                kwargs.pop('doc')
                kwargs.pop('method')
            except TypeError as e:
                raise click.BadParameter(e.message)
            configurations.append(kwargs)
        definitions.append([task, configurations])
    return definitions

def move_to_storage(id, kwargs):
    """
    Takes as dictionary of kwargs and moves the suffix of all keys starting
    with the string 'file:' to the storage medium, prepending a unique
    identifier. The path components are rewritten in storage tuple form and the
    modified dictionary is returned.

    It is assumed that the filestore is already created.
    """
    nkwargs = {}
    for k, v in kwargs.iteritems():
        if isinstance(v, basestring) and v.startswith('file:'):
            suffix = uuid.uuid4()
            v = v.replace('file:', '', 1)
            dest = unicode(suffix) + '_' + os.path.basename(v)
            shutil.copy2(v, storage.get_abs_path(id, dest))
            nkwargs[k] = (id, dest)
        else:
            nkwargs[k] = v
    return nkwargs
            

@main.command()
@click.option('--binarize', '-b', multiple=True, callback=validate_definition,
              help='A configuration for a single binarization algorithm in '
              'the format algorithm:param1,param2;param1,param2;...')
@click.option('--ocr', '-o', multiple=True, callback=validate_definition, 
              help='A configuration for a single OCR engine in the format '
              'engine:param1,param2;param1,param2;...')
@click.option('--stats', '-s', multiple=True, callback=validate_definition,
              help='A configuration for a single post-OCR measure in the '
              'format measure:param1,param2;param1;param2...')
@click.option('--willitblend', 'blend',  default=False, help='Blend all '
              'output files into a single hOCR document.', is_flag=True)
@click.option('--grayscale', default=False, help='Skip grayscale '
              'conversion using the ITU-R 601-2 luma transform if the input '
              'documents are already in grayscale.', is_flag=True)
@click.option('--jobid', default=uuid.uuid4(), type=str, help='Force a job '
              'identifier. This may or may not be an UUID but it has to be an '
              'unused identifer.')
@click.option('--help-tasks', is_eager=True, is_flag=True, callback=help_tasks,
              help='Accesses the documentation of all tasks contained in '
              'nidaba itself and in configured plugins.')
@click.argument('files', type=click.Path(exists=True), nargs=-1, required=True)
def batch(files, binarize, ocr, stats, blend, grayscale, jobid, help_tasks):
    """
    Add a new job to the pipeline.
    """
    id = unicode(jobid)
    batch = Batch(id)
    click.echo(u'Preparing filestore\t\t[', nl=False),
    if storage.prepare_filestore(id) is None:
        click.secho(u'\u2717', fg='red', nl=False)
        click.echo(']')
        exit()
    for doc in files:
        shutil.copy2(doc, storage.get_abs_path(id, os.path.basename(doc)))
        batch.add_document((id, os.path.basename(doc)))
    click.secho(u'\u2713', fg='green', nl=False)
    click.echo(']')
    click.echo(u'Building batch\t\t\t[', nl=False)
    batch.add_step()
    if not grayscale:
        batch.add_tick()
        batch.add_task('img.rgb_to_gray')
    if binarize:
        batch.add_tick()
        for alg in binarize:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task(alg[0], **kwargs)
    if ocr:
        batch.add_tick()
        for alg in ocr:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task(alg[0], **kwargs)
    if stats:
        batch.add_tick()
        for alg in stats:
            for kwargs in alg[1]:
                kwargs = move_to_storage(id, kwargs)
                batch.add_task(alg[0], **kwargs)
    if blend:
        batch.add_step()
        batch.add_tick()
        batch.add_task('postprocessing.blend_hocr')
    batch.run()
    click.secho(u'\u2713', fg='green', nl=False)
    click.echo(']')
    click.echo(id)


@main.command()
def worker():
    """
    Starts a celery worker.
    """
    celery.app.worker_main(argv=sys.argv[:1])


@main.command()
def config():
    """
    Displays the current configuration.
    """
    pprint(nidaba_cfg)


@main.command()
@click.argument('job_id', nargs=1, type=str)
def status(job_id):
    """
    Diplays the status and results of jobs.
    """
    batch = Batch(job_id)
    state = batch.get_state()
    print(state)
    if state == 'SUCCESS':
        ret = batch.get_results()
        if ret is None:
            print('Something somewhere went wrong.')
            print('Please contact your friendly nidaba support technician.')
        else:
            for doc in ret:
                click.echo(doc['root'][1].encode('utf-8') + u' \u2192 ' + 
                      storage.get_abs_path(*doc['doc']).encode('utf-8'))
    elif state == 'FAILURE':
        ret = batch.get_errors()
        if ret is None:
            print('Something somewhere went wrong.')
        else:
            for fun in ret:
                print(fun[0]['method'].encode('utf-8'),
                      'failed while operating on',
                      fun[0]['doc'][1].encode('utf-8'),
                      'which is based on',
                      fun[1]['root'][1].encode('utf-8'))
