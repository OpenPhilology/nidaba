# -*- coding: utf-8 -*-
# This module contains all celery tasks. All tasks should be try-except safed,
# to guarantee A:graceful recovery from a failed OCR task, and B:immediate
# point-of-failure indentification for debugging purposes, or to easily identify
# bad OCR data.

from . import celeryconfig
from . import irisconfig
from . import algorithms
from . import tesseract
from . import storage
from . import leper
from . import merge_hocr
from .irisexceptions import IrisNoSuchAlgorithmException

import uuid
import logging
import inspect
import time
import gzip
import zipfile
import requests
import os

from celery import Celery
from celery import group
from celery import chord
from celery.task.sets import TaskSet
from celery.utils.log import get_task_logger

app = Celery(main='tasks', broker=celeryconfig.BROKER_URL)
app.config_from_object(celeryconfig)

# Application tasks
# In general they should be sorted in the order of execution, e.g. an image
# should be converted to grayscale before running the binarization algorithm(s)
# on it.

@app.task(name=u'rgb_to_gray')
def rgb_to_gray(doc, method=u'rgb_to_gray'):
    """Converts an arbitrary bit depth image to grayscale and writes it back
    appending a suffix.
    
    Args:
        doc (unicode): The filename of the input document.
        id (unicode): The unique id underneath all files are situated.
        method (unicode): The suffix string appended to all output files.

    Returns:
        unicode: Path of the output file.
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method)
    return storage.get_storage_path(leper.rgb_to_gray(input_path, output_path))

@app.task(name=u'binarize')
def binarize(doc, method=u'binarize', algorithm=u'sauvola', thresh=10,
        factor=0.3, mincount=50, bgval=255, smoothx=2, smoothy=2):
    """Binarizes an input document utilizing ether Sauvola or Otsu
    thresholding. Expects grayscale images as input.
    
    Args:
        doc (unicode): The filename of the input document.
        id (unicode): The unique id underneath all files are situated.
        method (unicode): The suffix string appended to all output files.
        algorithm (unicode): Either ''sauvola'' or ''otsu''
        thresh (int): Threshold/window size used by either algorithm.
        factor (float): (sauvola only) Threshold reduction factor.
        mincount (int): (otsu only) Min theshold on counts in a tile.
        bgval (int): (otsu only) Target background value.
        smoothx (int): (otsu only) Half-width of block convolution kernel width.
        smoothy (int): (otsu only) Half-width of block convolution kernel height.

    Returns:
        unicode: Path of the output file.
    """
    input_path = storage.get_abs_path(*doc)
    if algorithm == u'sauvola':
        output_path = storage.insert_suffix(input_path, method, algorithm,
                                            unicode(thresh), unicode(factor))
        return storage.get_storage_path(leper.sauvola_binarize(input_path,
            output_path, thresh, factor))
    elif algorithm == u'otsu':
        output_path = storage.insert_suffix(input_path, method, algorithm,
                                            unicode(thresh), unicode(mincount),
                                            unicode(bgval), unicode(smoothx),
                                            unicode(smoothy))
        return storage.get_storage_path(leper.otsu_binarize(input_path,
            output_path, thresh, mincount, bgval, smoothx, smoothy))
    else:
        raise IrisNoSuchAlgorithmException('No binarization ' + method + ' available')

@app.task(name=u'dewarp')
def dewarp(doc, method=u'dewarp'):
    """Removes perspective distortion (as commonly exhibited by overhead scans)
    from an 1bpp input image.
    
    Args:
        doc (unicode): The filename of the input document.
        id (unicode): The unique id underneath all files are situated.
        method (unicode): The suffix string appended to all output files.

    Returns:
        unicode: Path of the output file.
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method)
    return storage.get_storage_path(leper.dewarp(input_path, output_path))

@app.task(name=u'deskew')
def deskew(doc, method=u'deskew'):
    """Removes skew (rotational distortion) from an 1bpp input image.
    
    Args:
        doc (unicode): The filename of the input document.
        id (unicode): The unique id underneath all files are situated.
        method (unicode): The suffix string appended to all output files.

    Returns:
        unicode: Path of the output file.
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method)
    return storage.get_storage_path(leper.deskew(input_path, output_path))

@app.task(name=u'blend_hocr')
def deskew(docs, language=u'',  method=u'blend_hocr'):
    """Blends multiple hOCR files using the algorithm from Bruce Robertsons
    rigaudon. It requires a working spell checking for the input document's
    language; otherwise all matched bboxes will be bunched together without any
    scoring.
    
    Args:
        docs [(id, path), ...]: A list of storage module tupels that will be
        merged into a single output document.
        language (unicode): Language used for spell-checking based scoring. If
        not defined no scoring will be used.
        method (unicode): The suffix string appended to the output file.


    Returns:
        unicode: Path of the output file.
    """
    input_path = storage.get_abs_path(*docs[0])
    output_path = storage.insert_suffix(input_path, method)
    return merge_hocr.merge(docs, language, storage.get_storage_path(output_path))

@app.task(name=u'ocr_tesseract')
def ocr_tesseract(doc, method=u'ocr_tesseract', languages=None):
    """Runs tesseract on an input document.
    
    Args:
        doc (unicode): The filename of the input document.
        id (unicode): The unique id underneath all files are situated.
        method (unicode): The suffix string appended to all output files.
        languages (list of unicode): A list of languages for the tesseract language model.
        
    Returns:
        unicode: Path of the output file.
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method, *languages)
    return storage.get_storage_path(tesseract.ocr(input_path, output_path, languages))

@app.task(name=u'ocr_ocropus')
def ocr_ocropus(config):
    """Runs ocropus on the input documents set."""
    pass

