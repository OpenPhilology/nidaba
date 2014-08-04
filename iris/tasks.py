# -*- coding: utf-8 -*-
# This module contains all celery tasks. All tasks should be try-except safed,
# to guarantee A:graceful recovery from a failed OCR task, and B:immediate
# point-of-failure indentification for debugging purposes, or to easily identify
# bad OCR data.

import celeryConfig
import irisconfig
import uuid
import logging
import inspect
import time
import gzip
import zipfile
import requests
import algorithms
import leper
import os

from celery import Celery
from celery import group
from celery import chord
from celery.task.sets import TaskSet
from celery.utils.log import get_task_logger

app = Celery(main='tasks', broker=celeryConfig.BROKER_URL)
app.config_from_object('celeryConfig')

@app.task(name='ocr_entry')
def ocr_batch(config):
    """Entry point for the whole ocr pipeline. Expects a configuration object
    detailing each sub step working on a group of documents."""
    pass

# Application tasks
# In general they should be sorted in the order of execution, e.g. an image
# should be converted to grayscale before running the binarization algorithm(s)
# on it.

@app.task(name='rgb_to_gray')
def rgb_to_gray(id=u'', in_files=[], out_suffix=u'gray'):
    """Converts arbitrary bit depth images in input_dir and writes then into
       the output directory."""
    @app.task(name='ctg_util')
    def ctg_util(input, output):
        return leper.rgb_to_gray(input, output)
    g = group()
    for input in in_files:
        (o, e) = os.path.splitext(input)
        output = o + u'_' + out_suffix + e
        g |= ctg_util.s(storage.get_abs_path(id, input),
                storage.get_abs_path(id, output))
    g.apply_async()
    

@app.task(name='binarize')
def binarize(in_files=[], configuration={}):
    """Binarizes a group of input documents and writes them into an output directory. Expects grayscale input"""

@app.task(name='dewarp')
def dewarp(in_files=[], id=u'', out_suffix=u'dewarp'):
    """Removes perspective distortion (as commonly exhibited by overhead scans)
    from images in input_dir and writes them into an output directory.  Expects
    binarized input."""
    pass

@app.task(name='deskew')
def deskew(in_files=[], id=u'', out_suffix=u'deskew'):
    """Removes skew (rotational distortion) from a set of images in input_dir
    and writes them into an output directory. Expects binarized input."""
    pass

@app.task(name='ocr_tesseract')
def ocr_tesseract(config):
    """Runs tesseract on the input document set."""
    pass

@app.task(name='ocr_ocropus')
def ocr_ocropus(config):
    """Runs ocropus on the input documents set."""
    pass

