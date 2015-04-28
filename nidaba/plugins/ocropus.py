# -*- coding: utf-8 -*-
"""
nidaba.plugins.ocropus
~~~~~~~~~~~~~~~~~~~~~~

Plugin implementing an interface to the `ocropus
<http://github.com/tmbdev/ocropy>`_ OCR engine.

It requires working ocropus-* tools in your execution path. Please have a look
at the website for installation instructions. 

.. important::
    If you are not requiring specific functionality of ocropus please consider
    using the :mod:`kraken <nidaba.plugins.kraken>` plugin. Kraken does not
    require working around oddities in input argument acceptance and is
    generally more well-behaved than ocropus.

.. note::
    ocropus uses a peculiar implementation of splitext removing all characters
    after the first dot to determine the output path of OCR results. We
    mitigate this by appending a unique UUID for each input file before the
    first dot. Unfortunately, this process causes the loss of all processing
    info carried in the file name.
"""

from __future__ import absolute_import

import subprocess
import glob
import os
import re
import shutil
import uuid

from distutils import spawn
from nidaba import storage
from nidaba.config import nidaba_cfg
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaOcropusException
from nidaba.nidabaexceptions import NidabaPluginException

def setup(*args, **kwargs):
    if None in [spawn.find_executable('ocropus-rpred'),
                spawn.find_executable('ocropus-gpageseg'),
                spawn.find_executable('ocropus-hocr')]:
        raise NidabaPluginException('Prerequisites for ocropus module not installed.')

@app.task(base=NidabaTask, name=u'nidaba.ocr.ocropus')
def ocr_ocropus(doc, method=u'ocr_ocropus', model=None):
    """
    Runs ocropus on an input document.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files
        model (unicode): Identifier for the font model to use

    Returns:
        (unicode, unicode): Storage tuple for the output file

    """
    input_path = storage.get_abs_path(*doc)
    output_path = os.path.splitext(storage.insert_suffix(input_path, method,
                                                         model))[0] + '.html'
    model = storage.get_abs_path(*(nidaba_cfg['ocropus_models'][model]))
    return storage.get_storage_path(ocr(input_path, output_path, model))


def _allsplitext(path):
    """
    Split all the pathname extensions, so that "a/b.c.d" -> "a/b", ".c.d"

    Args:
        path (unicode): A unicode object containing a file path.

    Returns:
        (tuple): Result containing firstly the path without extensions and
                 secondly the extracted extensions.
    """
    match = re.search(ur'((.*/)*[^.]*)([^/]*)', path)
    if not match:
        return (path, u'')
    else:
        return (match.group(1), match.group(3))


def ocr(imagepath, outputfilepath, modelpath):
    """
    Scan a single image with ocropus.

    Reads a single image file from ```imagepath``` and writes the recognized
    text as in hOCR format into outputfilepath. Ocropus's superfluous
    intermediate output remains in the directory imagepath is located in.

    Args:
        imagepath (unicode): Path of the input file
        outputfilepath (unicode): Path of the output file
        modelpath (unicode): Path of the recognition model. Must be a pyrnn.gz
                             pickle dump interoperable with ocropus-rpred.

    Returns:
        (unicode): A string of the output file that is actually written. As
                   Ocropus rewrites output file paths without notice it may be
                   different from the ```outputfilepath``` argument.

    Raises:
        NidabaOcropusException: Ocropus somehow failed. The error output is
                                contained in the message but as it is de facto
                                unusable as a library it's impossible to deduct
                                the nature of the problem.
    """

    fglob = _allsplitext(imagepath)[0]
    # ocropus removes everything after the first . anyway so we do it
    # preemptively here and add a stable unique identifier to ensure uniqueness
    # of output.
    outputfilepath = _allsplitext(outputfilepath)[0]
    outputfilepath += '_' + str(uuid.uuid5(uuid.NAMESPACE_URL,
                                           outputfilepath.encode('utf-8')))
    working_dir = os.path.dirname(outputfilepath)

    # ocropus is stupid and needs the input file to end in .bin.png
    shutil.copyfile(imagepath, fglob + '.bin.png')
    imagepath = fglob + '.bin.png'
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    # page layout analysis
    p = subprocess.Popen(['ocropus-gpageseg', '-n', imagepath.encode('utf-8')],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env, cwd=working_dir)
    out, err = p.communicate()
    print(out)
    if p.returncode:
        raise NidabaOcropusException(err)

    # text line recognition
    p = subprocess.Popen(['ocropus-rpred', '-q', '-m',
                          modelpath.encode('utf-8')] + glob.glob(fglob +
                                                                 '/*.bin.png'),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env, cwd=working_dir)
    out, err = p.communicate()
    if p.returncode:
        raise NidabaOcropusException(err)

    # recognition hOCR assembly
    # page segmentation is always converted to PNG
    p = subprocess.Popen(['ocropus-hocr', imagepath.encode('utf-8'), '-o',
                          outputfilepath.encode('utf-8')],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env, cwd=working_dir)
    out, err = p.communicate()
    if p.returncode:
        raise NidabaOcropusException(err)
    return outputfilepath
