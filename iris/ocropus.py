# -*- coding: utf-8 -*-
import errno
import subprocess
import glob
import irisconfig
import re

from irisexceptions import IrisOcropusException

def _allsplitext(path):
    """Split all the pathname extensions, so that "a/b.c.d" -> "a/b", ".c.d" """
    match = re.search(ur'((.*/)*[^.]*)([^/]*)',path)
    if not match:
        return path,""
    else:
        return match.group(1),match.group(3)

def ocr(imagepath, outputfilepath, modelpath):
    """
    Scan a single image with ocropus.
    """

    # page layout analysis
    p = subprocess.Popen(['ocropus-gpageseg', '--usefilename',
        imagepath.encode('utf-8')], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise IrisOcropusException(err)

    fglob = _allsplitext(imagepath)[0]
    # text line recognition
    p = subprocess.Popen(['ocropus-rpred', '-m' , modelpath.encode('utf-8'),
        (fglob + u'/*').encode('utf-8')], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise IrisOcropusException(err)

    # recognition hOCR assembly
    # page segmentation is always converted to PNG
    p = subprocess.Popen(['ocropus-hocr', (fglob +
        u'.pseg.png').encode('utf-8'), '-o', outputfilepath.encode('utf-8')],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise IrisOcropusException(err)
    return outputfilepath
