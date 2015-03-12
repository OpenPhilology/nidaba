# -*- coding: utf-8 -*-

from __future__ import absolute_import

import subprocess
import glob
import re
import shutil

from nidaba.config import nidaba_cfg
from nidaba.nidabaexceptions import NidabaOcropusException


def _allsplitext(path):
    """
    Split all the pathname extensions, so that "a/b.c.d" -> "a/b", ".c.d"

    Args:
        path (unicode): A unicode object containing a file path.

    Returns:
        A tuple containing two elements. Firstly the path without extensions
        and secondly the extracted extensions.
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
       A unicode string of the output file that is actually written. As Ocropus
       rewrites output file paths without notice it may be different from the
       ```outputfilepath``` argument.

    Raises:
        NidabaOcropusException: Ocropus somehow failed. The error output is
        contained in the message but as it is de facto unusable as a library
        it's impossible to make deduct the nature of the problem.
    """

    fglob = _allsplitext(imagepath)[0]

    # ocropus is stupid and needs the input file to end in .bin.png
    shutil.copyfile(imagepath, fglob + '.bin.png')
    imagepath = fglob + '.bin.png'
    # page layout analysis
    if nidaba_cfg['legacy_ocropus']:
        flag = ''
    else:
        flag = '-n'
    p = subprocess.Popen(['ocropus-gpageseg', flag, imagepath.encode('utf-8')],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise NidabaOcropusException(err)

    # text line recognition
    p = subprocess.Popen(['ocropus-rpred', '-q', '-m',
                         modelpath.encode('utf-8')] + glob.glob(fglob +
                         u'/*.bin.png'), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise NidabaOcropusException(err)

    # recognition hOCR assembly
    # page segmentation is always converted to PNG
    p = subprocess.Popen(['ocropus-hocr', imagepath.encode('utf-8'), '-o',
                          outputfilepath.encode('utf-8')],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise NidabaOcropusException(err)
    return outputfilepath
