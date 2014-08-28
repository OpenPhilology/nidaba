# -*- coding: utf-8 -*-
# This module contains all celery tasks. All tasks should be try-except safed,
# to guarantee A:graceful recovery from a failed OCR task, and B:immediate
# point-of-failure indentification for debugging purposes, or to easily identify
# bad OCR data.

import celeryconfig
import irisconfig
import algorithms
import tesseract
import uuid
import logging
import inspect
import time
import gzip
import zipfile
import requests
import leper
import os
import storage

from celery import Celery
from celery import group
from celery import chord
from celery.task.sets import TaskSet
from celery.utils.log import get_task_logger

app = Celery(main='tasks', broker=celeryconfig.BROKER_URL)
app.config_from_object('celeryconfig')

# ------------------------------------------------------------------------------------------
# The tasks. -------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------



# @app.task(name='edit_distance_task')
# def edit_distance_task(str1, str2):
#     algorithms.edit_distance(str1, str2)
    

# @app.task(name='http_download')
# def http_download(username, password, url, path, fsaddr=irisconfig.FTP_ADDR):
#     """Download the contents of a url and store the result at the specified path."""

#     filestore = mount_filestore(fsaddr, username, password)
#     r = requests.get(url, stream=True)
#     if r.status_code == 200:
#         with filestore.open(path, 'w+') as f:
#             for chunk in r.iter_content():
#                 f.write(chunk)

#     filestore.close()
#     return path

# @app.task(name='unzip_archive')
# def unzip_archive(username, password, src, dst=None, fsaddr=irisconfig.FTP_ADDR):
#     """Extract the contents of a zip archive and store them at the desired directory."""

#     filestore = mount_filestore(fsaddr, username, password)
#     extractdir = dst if dst is not None else fs.path.dirname(src)

#     with filestore.open(src) as fh:    # Get a standard python file-like object from the filestore.
#         with zipfile.ZipFile(fh) as zfh:    # Get a zip object from the file object.
#             for name in zfh.namelist():                # For every item in that zip archive...
#                 with zfh.open(name) as extracted_file:     # Get a standart python file-like object from which we can read decompressed data.
#                     realname = fs.path.basename(name)
#                     filepath = fs.path.join(extractdir, realname)
#                     filestore.createfile(filepath)
#                     filestore.setcontents(filepath, extracted_file.read())

#     filestore.close()
#     return extractdir

# @app.task(name='get_archive.org_archive')
# def get_org_archive(archive_name, username, password, fsaddr=irisconfig.FTP_ADDR):
#     """Retrieve an archive.org archive."""
#     filestore = mount_filestore(fsaddr,  username, password)
#     url = archive_url_format.format(archive_name, '_tif.zip')

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
>>>>>>> tasks
    

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
def ocr_tesseract(imgpath, outputpath, languages):
    """Runs tesseract on an input document."""
        return ocr(imgpath, outputpath, languages)

@app.task(name='ocr_ocropus')
def ocr_ocropus(config):
    """Runs ocropus on the input documents set."""
    pass

