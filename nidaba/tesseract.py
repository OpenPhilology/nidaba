# -*- coding: utf-8 -*-
"""
nidaba.tesseract
~~~~~~~~~~~~~~~~

Wrappers around the tesseract OCR engine.
"""
from __future__ import absolute_import

import os
import errno
import subprocess
import glob

from nidaba.nidabaexceptions import NidabaTesseractException
from nidaba.config import nidaba_cfg

# More readable aliases for tesseract's language abbreviations.
greek = 'grc'

# Formats for filtering when ocring directories.
fileformats = ('png', 'tiff', 'jpg')


def ocr(imagepath, outputfilepath, languages):
    """
    Scan a single image with tesseract using the specified language,
    and writing output to the specified file.

    Args:
        imagepath (unicode): Path to the image file
        outputfilepath (unicode): Path to the output file. Tesseract will
                                  independently append either .html or .hocr to
                                  this path.
        languages (list): A list of strings containing valid tesseract language
                          descriptions.
    Returns:
        unicode: Path of the output file.

    Raise:
        NidabaTesseractException: Tesseract quit with a return code other than
                                  0.
    """
    abs_in = os.path.abspath(os.path.expanduser(imagepath))
    abs_out = os.path.abspath(os.path.expanduser(outputfilepath))
    p = subprocess.Popen(['tesseract', '-l', '+'.join(languages), abs_in,
                         abs_out, 'hocr'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if nidaba_cfg['legacy_tesseract']:
        resultpath = abs_out + '.html'
    else:
        resultpath = abs_out + '.hocr'
    out, err = p.communicate()
    if p.returncode:
        raise NidabaTesseractException(err)
    return resultpath


def ocrdir(dirpath, outputdir, languages):
    """
    Scans all documents deemed to be image files in a directory (recursively).

    Args:
        dir (unicode): Path to the directory containing the image files.
        outputdir (unicode): Path to the output directory. It will be created
                             if it doesn't exist.
        languages (list): A list of strings containing valid tesseract language
                          descriptions.
    Returns:
        list: Paths of the output files.

    Raise:
        NidabaTesseractException: Tesseract quit with a return code other than
                                  0.
        OSError: The output directory couldn't be created.
        Exception: The input directory does not exist.
    """

    if not os.path.isdir(dirpath):
        raise Exception('Directory did not exist!')

    try:
        os.makedirs(outputdir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
    results = []
    for ext in fileformats:
        for imgpath in glob.glob(os.path.join(dirpath, '*.%s' % ext)):
            filename = os.path.basename(os.path.normpath(imgpath))
            outfile = os.path.join(outputdir, filename)
            ocr(imgpath, outfile, languages)
            results.append(outfile)

    return results
