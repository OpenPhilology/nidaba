#! /usr/bin/env python
# -*- coding: utf-8 -*-
# This modul contains all entry points to the various components of iris.

from . import iris
from . import irisconfig
from . import storage

from pprint import pprint

import argparse
import uuid
import shutil
import os.path

def main():
    parser = argparse.ArgumentParser(description=u'Sends jobs to iris and\
                                    retrieves their status.',
                                    epilog=u'This iris may or may not have\
                                    Super Cow Powers.')
    subparsers = parser.add_subparsers()

    # Command line parameters for querying a job ID
    statusparser = subparsers.add_parser('status', help='Displays the status of a job')
    statusparser.add_argument('jobid', help='The unique job ID returned by batch.')
    statusparser.set_defaults(func=status)

    # Command line parameters for configuration file display
    configparser = subparsers.add_parser('config', help='Show the current iris configuration.')
    configparser.set_defaults(func=config)

    # Command line parameters for a new job
    batchparser = subparsers.add_parser('batch', help='Put a new batch into the pipeline.')
    batchparser.add_argument('files', help=u'A list of input files to be converted\
                              using the pipeline. They will be copied into a\
                              directory beneath STORAGE_PATH.', nargs='+')
    batchparser.add_argument('--binarize', help=u'A list of binarization options in\
                        the format algorithm:t1 algorithm2:t1,t2,... where\
                        algorithm is either otsu or sauvola and t1,.. are\
                        integer thresholds.', nargs='+', default=[u'sauvola:40'])
    batchparser.add_argument('--ocr', help=u'A list of OCR engine options in the\
                        format engine:language1,language2 engine:model1, model2\
                        where engine is either tesseract or ocropus and\
                        language* is a tesseract language model and model1 is\
                        a ocropus model defined in irisconfig.', nargs='+', default=[u'tesseract:eng'])
    batchparser.add_argument('--willitblend', help=u'Blends all output files into a\
                             single hOCR document.', action='store_true', default=False)
    batchparser.add_argument('--grayscale', help=u'Input file are already 8bpp\
                             RGB grayscale.', action='store_true', default=False)

    batchparser.set_defaults(func=batch)

    args = parser.parse_args()
    args.func(args)

def batch(args):

    print 'Building actions array...',
    # build actions array
    batch_def = [[]]
    if not args.grayscale:
        batch_def[0].append([{u'method': u'rgb_to_gray'}])
    binarizations = []
    # build binarization(s)
    for bin in args.binarize:
        (alg, _, threshs) = bin.partition(u':')
        for t in threshs.split(u','):
            binarizations.append({u'method': u'binarize', u'algorithm': alg, u'thresh': int(t)})
    batch_def[0].append(binarizations)
    # build ocr conversions
    conversions = []
    for ocr in args.ocr:
        (engine, _, params) = ocr.partition(u':')
        if engine == u'tesseract':
            conversions.append({u'method': u'ocr_tesseract', u'languages': params.split(u',')})
        elif engine == u'ocropus':
            for model in params.split(u','):
                m = irisconfig.OCROPUS_MODELS[model]
                conversions.append({u'method': u'ocr_ocropus', u'model': m})
        else:
            print('WARNING: OCR engine ' + engine.encode('utf-8') + ' not known.')
    batch_def[0].append(conversions)
    if args.willitblend:
        batch_def.append([[{u'method': u'blend_hocr'}]])
    print('done.')
    id = unicode(uuid.uuid4())
    print 'Preparing filestore...',
    if storage.prepare_filestore(id) == None:
        print('failed.')
        exit()
    else:
        print('done.')
    input = []
    print 'Copying files to store...',
    for doc in args.files:
        shutil.copy2(doc, storage.get_abs_path(id, os.path.basename(doc)))
        input.append(os.path.basename(doc))
    s = iris.batch({ u'batch_id': id,
        u'input_files': input,
        u'actions': batch_def
    })
    print('done.')
    print(s)

def config(args):
    for field in dir(irisconfig):
        if not field.startswith('__'):
            print('* ' + field.encode('utf-8'))
            pprint(getattr(irisconfig, field))

def status(args):
    state = iris.get_state(args.jobid)
    print(state)
    if state == 'SUCCESS':
        ret = iris.get_results(args.jobid)
        if ret == None:
            print('Something somewhere went wrong.')
            print('Please contact your friendly iris support technician.')
        else:
            for doc in ret:
                print('\t' + storage.get_abs_path(*doc).encode('utf-8'))
