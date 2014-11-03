#! /usr/bin/env python
# -*- coding: utf-8 -*-
# This modul contains all entry points to the various components of iris.

from . import iris
from . import irisconfig
from . import storage

from pprint import pprint

import argparse
import uuid

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
                        using the pipeline', nargs='+')
    batchparser.add_argument('--binarize', help=u'A list of binarization options in\
                        the format algorithm:t1 algorithm2:t1,t2,... where\
                        algorithm is either otsu or sauvola and t1,.. are\
                        integer thresholds.', nargs='+')
    batchparser.add_argument('--ocr', help=u'A list of OCR engine options in the\
                        format engine:language1,language2 engine:model1, model2\
                        where engine is either tesseract or ocropus and\
                        language* is a tesseract language model and model1 is\
                        a ocropus model defined in irisconfig.', nargs='+')
    batchparser.add_argument('--willitblend', help=u'Blends all output files into a\
                        single hOCR document.', type=int, choices=[0,1])
    batchparser.set_defaults(func=batch)

    args = parser.parse_args()
    args.func(args)

def batch(args):
    

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
