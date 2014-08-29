# -*- coding: utf-8 -*-
import os
import errno
import subprocess
import glob

from irisexceptions import IrisTesseractException

#More readable aliases for tesseract's language abbreviations.
greek = 'grc'

#Formats for filtering when ocring directories.
fileformats = ('png', 'tiff', 'jpg')

def ocr(imagepath, outputfilepath, languages):
    """
    Scan a single image with tesseract using the specified language,
    and writing output to the specified file. Returns a 3 tuple of the
    format (absolute path to output, tesseract's stdout, tesseract's 
    stderr).
    """
    abs_in = os.path.abspath(os.path.expanduser(imagepath))
    abs_out = os.path.abspath(os.path.expanduser(outputfilepath))
    p = subprocess.Popen(['tesseract', '-l', '+'.join(languages), abs_in,
        abs_out, 'hocr'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    resultpath = abs_out + '.html'
    out, err = p.communicate()
    if p.returncode:
        raise IrisTesseractException(err)
    return resultpath


def ocrdir(dirpath, outputdir, language):
    """
    Scan a directory of images with tesseract using the specified
    language, and writing to the specified directory. The directory
    will be created if it does not exist. Returns the path of the dir
    containing the results.
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
            ocr(imgpath, outfile, language)
            results.append(outfile)

    return results

    
if __name__ == '__main__':
    pass
