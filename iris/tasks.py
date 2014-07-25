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

from celery import Celery
from celery import group
from celery import chord
from celery.task.sets import TaskSet
from celery.utils.log import get_task_logger
from requests import HTTPError, ConnectionError, Timeout
from fs import ftpfs, path, errors
from cStringIO import StringIO

app = Celery(main='tasks', broker=celeryConfig.BROKER_URL)
app.config_from_object('celeryConfig')

archive_url_format = 'http://www.archive.org/download/{0}/{0}{1}'

# Meta tasks
# Meta tasks execute application tasks and facilitate data exchange between sub
# tasks in the pipeline.

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
def rgb_to_gray(id, input_dir, output_dir):
    """Converts arbitrary bit depth images in input_dir and writes then into the output directory."""
    pass

@app.task(name='binarize')
def binarize(config):
    """Binarizes a group of input documents and writes them into an output directory. Expects grayscale input"""
    pass

@app.task(name='dewarp')
def deskew(id, input_dir, output_dir):
    """Removes perspective distortion (as commonly exhibited by overhead scans)
    from images in input_dir and writes them into an output directory.  Expects
    binarized input."""
    pass

@app.task(name='deskew')
def deskew(id, input_dir, output_dir):
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
