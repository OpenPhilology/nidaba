#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module encapsulates all shell callable functions of nidaba.
"""

from __future__ import absolute_import, print_function, unicode_literals

from nidaba import Batch, storage
from nidaba.config import nidaba_cfg
from pprint import pprint

import argparse
import uuid
import shutil
import os.path


def main():
    """
    Main function called by the hook installed by setuptools.
    """

    parser = argparse.ArgumentParser(description=u'Sends jobs to nidaba and\
                                    retrieves their status.',
                                     epilog=u'This nidaba may or may not have\
                                    Super Cow Powers.')
    subparsers = parser.add_subparsers()

    # Command line parameters for querying a job ID
    statusparser = subparsers.add_parser(
        'status', help='Displays the status of a job')
    statusparser.add_argument(
        'jobid', help='The unique job ID returned by batch.')
    statusparser.set_defaults(func=status)

    # Command line parameters for configuration file display
    configparser = subparsers.add_parser(
        'config', help='Show the current nidaba configuration.')
    configparser.set_defaults(func=config)

    # Command line parameters for a new job
    batchparser = subparsers.add_parser(
        'batch', help='Put a new batch into the pipeline.')
    batchparser.add_argument('files', help=u'A list of input files to be converted\
                              using the pipeline. They will be copied into a\
                              directory beneath STORAGE_PATH.', nargs='+')
    batchparser.add_argument('--binarize', help=u'A list of binarization options in\
                             the format\
                             algorithm:whsize=10;whsize=20,factor=0.7\
                             algorithm2:t1,... where algorithm is either otsu\
                             or sauvola and the parameters are a list of\
                             particular configuration of the algorithm where\
                             each configuration is a sequence of algorithmic\
                             parameters divided by ,.', nargs='+',
                             default=[u'sauvola:whsize=40'])
    batchparser.add_argument('--ocr', help=u'A list of OCR engine options in\
                             the format engine:language1,language2\
                             engine:model1, model2 where engine is either\
                             tesseract or ocropus and language* is a tesseract\
                             language model and model1 is a ocropus model\
                             defined in the nidaba config.', nargs='+')
    batchparser.add_argument('--willitblend', help=u'Blends all output files into a\
                             single hOCR document.', action='store_true',
                             default=False)
    batchparser.add_argument('--grayscale', help=u'Input file are already 8bpp\
                             RGB grayscale.', action='store_true',
                             default=False)

    batchparser.set_defaults(func=batch)

    args = parser.parse_args()
    args.func(args)


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


def batch(args):
    """
    Implements the batch subcommand of the nidaba binary.

    Args:
        args (argparse.Namespace): Parsed input object from argparse
    """

    id = unicode(uuid.uuid4())
    batch = Batch(id)
    print('Preparing filestore....', end=''),
    if storage.prepare_filestore(id) is None:
        print('failed.')
        exit()
    for doc in args.files:
        shutil.copy2(doc, storage.get_abs_path(id, os.path.basename(doc)))
        batch.add_document((id, os.path.basename(doc)))
    print('done.')
    print('Building batch...', end='')

    batch.add_step()
    if not args.grayscale:
        batch.add_tick()
        batch.add_task('img.rgb_to_gray')
    if args.binarize:
        batch.add_tick()
        for bin in args.binarize:
            (alg, _, params) = bin.partition(u':')
            for c in params.split(u';'):
                kwargs = dict(kwarg.split('=') for kwarg in c.split(",") if len(kwarg.split('=')) == 2)
                print(kwargs)
                kwargs = {key: int_float_or_str(val)
                          for key, val in kwargs.items()}
                batch.add_task('binarize.' + alg, **kwargs)
    if args.ocr:
        batch.add_tick()
        for ocr in args.ocr:
            (engine, _, params) = ocr.partition(u':')
            if engine == u'tesseract':
                batch.add_task('ocr.tesseract', languages=params.split(u','))
            elif engine == u'ocropus':
                for model in params.split(u','):
                    if model not in nidaba_cfg['ocropus_models']:
                        print('WARNING: ocropus model ' +
                              model.encode('utf-8') + ' not known.')
                    else:
                        batch.add_task('ocr.ocropus', model=model)
            else:
                print('WARNING: OCR engine ' + engine.encode('utf-8') + ' not\
                      known.')
    if args.willitblend:
        batch.add_step()
        batch.add_tick()
        batch.add_task('util.blend_hocr')
    batch.run()
    print('done.')
    print(id)


def config(args):
    """
    Implements the config display subcommand.
    """

    pprint(nidaba_cfg)


def status(args):
    """
    Implements the status subcommand.

    Args:
        args (argparse.Namespace): Parsed input object from argparse
    """

    batch = Batch(args.jobid)
    state = batch.get_state()
    print(state)
    if state == 'SUCCESS':
        ret = batch.get_results()
        if ret is None:
            print('Something somewhere went wrong.')
            print('Please contact your friendly nidaba support technician.')
        else:
            for doc in ret:
                print('\t' + storage.get_abs_path(*doc).encode('utf-8'))
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
