# -*- coding: utf-8 -*-
"""
nidaba.plugins.tesseract
~~~~~~~~~~~~~~~~~~~~~~~~

Plugin implementing an interface to tesseract

This plugin exposes tesseract's functionality as a task. It implements two ways
of calling tesseract, a direct method calling the tesseract executable and one
utilizing the C-API available from tesseract 3.02 and upwards.

The C-API requires a libtesseract shared object in the current library path and
training data in the configured tessdata directory:

.. code-block:: console

    # apt-get install libtesseract3 tesseract-ocr-$lang

Using the direct call method requires the tesseract binary installable by
executing:

.. code-block:: console

    # apt-get install tesseract-ocr

.. note::
    It is strongly encouraged to use the C-API whenever possible. It is
    supposedly stable while hOCR output file names change between tesseract
    versions.

.. note::
    Parameters in configuration files supersede command line parameters.
    Modular page segmentation utilizing zone files requires that the page
    segmentation mode may be set freely. Uncomment the line:

        tessedit_pageseg_mode 1

    in the default hocr configuration (in TESSDATA/configs/).

Configuration
~~~~~~~~~~~~~

implementation (default='capi')
    Selector for the call method. May either be `capi`, `direct` (tesseract
    hOCR output with .hocr extension), or `legacy` (tesseract hOCR output with
    .html extension).

tessdata (default='/usr/share/tesseract-ocr/')
    Path to load tesseract training data and configuration from. Has to be one
    directory level upwards from the actual tessdata directory
"""

from __future__ import unicode_literals, print_function, absolute_import

import subprocess
import StringIO
import ctypes
import os

from PIL import Image
from ctypes import POINTER
from distutils import spawn
from os.path import splitext
from celery.utils.log import get_task_logger

from nidaba.uzn import UZNWriter
from nidaba import storage
from nidaba.tei import TEIFacsimile
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaTesseractException
from nidaba.nidabaexceptions import NidabaPluginException


implementation = u'capi'
tessdata = u'/usr/share/tesseract-ocr/'

(RIL_BLOCK, RIL_PARA, RIL_TEXTLINE, RIL_WORD, RIL_SYMBOL) = map(ctypes.c_int,
                                                                xrange(5))

logger = get_task_logger(__name__)


class TessBaseAPI(ctypes.Structure):
    pass


class Pix(ctypes.Structure):
    pass


class TessResultIterator(ctypes.Structure):
    pass


class TessPageIterator(ctypes.Structure):
    pass


class TessResultRenderer(ctypes.Structure):
    pass


def setup(*args, **kwargs):
    if kwargs.get(u'implementation'):
        global implementation
        implementation = kwargs.get(u'implementation')
    if kwargs.get(u'tessdata'):
        global tessdata
        if isinstance(kwargs.get(u'tessdata'), list):
            tessdata = storage.get_abs_path(*kwargs.get(u'tessdata'))
        else:
            tessdata = kwargs.get(u'tessdata')
    if implementation == 'direct' and not spawn.find_executable('tesseract'):
        raise NidabaPluginException('No tesseract executable found')
    if implementation == 'capi':
        try:
            global tesseract, leptonica
            tesseract = ctypes.cdll.LoadLibrary('libtesseract.so.3')
            leptonica = ctypes.cdll.LoadLibrary('liblept.so')
        except:
            raise NidabaPluginException('Loading libtesseract/leptonica failed.')

        tesseract.TessBaseAPICreate.restype = POINTER(TessBaseAPI)

        tesseract.TessBaseAPIEnd.argtypes = [POINTER(TessBaseAPI)]
        tesseract.TessBaseAPIEnd.restype = None

        tesseract.TessBaseAPIDelete.argtypes = [POINTER(TessBaseAPI)]
        tesseract.TessBaseAPIDelete.restype = None

        tesseract.TessBaseAPIInit3.argtypes = [POINTER(TessBaseAPI),
                                               ctypes.c_char_p,
                                               ctypes.c_char_p]
        tesseract.TessBaseAPIInit3.restype = ctypes.c_int

        tesseract.TessBaseAPISetImage2.restype = None
        tesseract.TessBaseAPISetImage2.argtypes = [POINTER(TessBaseAPI),
                                                   POINTER(Pix)]

        tesseract.TessBaseAPIRecognize.argtypes = [POINTER(TessBaseAPI), POINTER(TessBaseAPI)]
        tesseract.TessBaseAPIRecognize.restype = ctypes.c_int

        tesseract.TessResultIteratorGetUTF8Text.restype = ctypes.c_char_p
        tesseract.TessResultIteratorGetUTF8Text.argtypes = [POINTER(TessResultIterator),
                                                            ctypes.c_int]

        tesseract.TessResultIteratorConfidence.argtypes = [POINTER(TessResultIterator),
                                                           ctypes.c_int]
        tesseract.TessResultIteratorConfidence.restype = ctypes.c_float

        tesseract.TessResultIteratorWordRecognitionLanguage.argtypes = [POINTER(TessResultIterator)]
        tesseract.TessResultIteratorWordRecognitionLanguage.restype = ctypes.c_char_p

        tesseract.TessVersion.restype = ctypes.c_char_p

        tesseract.TessBaseAPISetPageSegMode.argtypes = [POINTER(TessBaseAPI),
                                                        ctypes.c_int]
        tesseract.TessBaseAPISetPageSegMode.restype = None

        tesseract.TessBaseAPIProcessPages.argtypes = [POINTER(TessBaseAPI),
                                                      ctypes.c_char_p,
                                                      ctypes.c_char_p,
                                                      ctypes.c_int,
                                                      POINTER(TessResultRenderer)]
        tesseract.TessBaseAPIProcessPages.restype = ctypes.c_int

        tesseract.TessBaseAPIAnalyseLayout.argtypes = [POINTER(TessBaseAPI)]
        tesseract.TessBaseAPIAnalyseLayout.restype = POINTER(TessPageIterator)

        tesseract.TessPageIteratorIsAtBeginningOf.argtypes = [POINTER(TessPageIterator),
                                                              ctypes.c_int]
        tesseract.TessPageIteratorIsAtBeginningOf.restype = ctypes.c_int

        tesseract.TessPageIteratorBoundingBox.argtypes = [POINTER(TessPageIterator),
                                                          ctypes.c_int,
                                                          POINTER(ctypes.c_int),
                                                          POINTER(ctypes.c_int),
                                                          POINTER(ctypes.c_int),
                                                          POINTER(ctypes.c_int)]
        tesseract.TessPageIteratorBoundingBox.restype = ctypes.c_int

        tesseract.TessBaseAPIGetIterator.argtypes = [POINTER(TessBaseAPI)]
        tesseract.TessBaseAPIGetIterator.restype = POINTER(TessResultIterator)

        tesseract.TessResultIteratorGetPageIterator.argtypes = [POINTER(TessResultIterator)]
        tesseract.TessResultIteratorGetPageIterator.restype = POINTER(TessPageIterator)

        tesseract.TessResultIteratorNext.argtypes = [POINTER(TessResultIterator), ctypes.c_int]
        tesseract.TessResultIteratorNext.restype = ctypes.c_int

        tesseract.TessResultIteratorDelete.argtypes = [POINTER(TessResultIterator)]
        tesseract.TessResultIteratorDelete.restype = None

        tesseract.TessPageIteratorDelete.argtypes = [POINTER(TessPageIterator)]
        tesseract.TessPageIteratorDelete.restype = None

        leptonica.pixRead.argtypes = [ctypes.c_char_p]
        leptonica.pixRead.restype = POINTER(Pix)

        leptonica.pixDestroy.argtypes = [POINTER(POINTER(Pix))]
        leptonica.pixDestroy.restype = None

        tesseract.TessBaseAPIGetHOCRText.argtypes = [POINTER(TessBaseAPI), ctypes.c_int]
        tesseract.TessBaseAPIGetHOCRText.restype = ctypes.c_char_p


@app.task(base=NidabaTask, name=u'nidaba.segmentation.tesseract')
def segmentation_tesseract(doc, method=u'segment_tesseract'):
    """
    Performs page segmentation using tesseract's built-in algorithm and writes
    a TEI XML segmentation file.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files.

    Returns:
        Two storage tuples with the first one containing the segmentation and
        the second one being the file the segmentation was calculated upon.
    """
    input_path = storage.get_abs_path(*doc)
    output_path = splitext(storage.insert_suffix(input_path, method))[0] + '.xml'

    ver = tesseract.TessVersion()
    if int(ver.split('.')[0]) < 3 or int(ver.split('.')[1]) < 2:
        raise NidabaTesseractException('libtesseract version is too old. Set '
                                       'implementation to direct.')
    api = tesseract.TessBaseAPICreate()
    rc = tesseract.TessBaseAPIInit3(api, tessdata.encode('utf-8'), None)
    if (rc):
        tesseract.TessBaseAPIDelete(api)
        raise NidabaTesseractException('Tesseract initialization failed.')

    # only do segmentation and script detection
    tesseract.TessBaseAPISetPageSegMode(api, 2)
    pix = leptonica.pixRead(input_path.encode('utf-8'))
    tesseract.TessBaseAPISetImage2(api, pix)
    it = tesseract.TessBaseAPIAnalyseLayout(api)
    leptonica.pixDestroy(ctypes.byref(pix))
    x0, y0, x1, y1 = (ctypes.c_int(), ctypes.c_int(), ctypes.c_int(),
                      ctypes.c_int())

    # initialize XML file
    tei = TEIFacsimile()
    tei.document(Image.open(input_path).size, os.path.join(*doc))
    tei.title = os.path.basename(doc[1])
    tei.add_respstmt('tesseract', 'page segmentation')

    while True:
        if tesseract.TessPageIteratorIsAtBeginningOf(it, RIL_TEXTLINE):
            tesseract.TessPageIteratorBoundingBox(it,
                                                  RIL_TEXTLINE,
                                                  ctypes.byref(x0),
                                                  ctypes.byref(y0),
                                                  ctypes.byref(x1),
                                                  ctypes.byref(y1))
            tei.add_line((x0.value, y0.value, x1.value, y1.value))
        if tesseract.TessPageIteratorIsAtBeginningOf(it, RIL_WORD):
            tesseract.TessPageIteratorBoundingBox(it,
                                                  RIL_WORD,
                                                  ctypes.byref(x0),
                                                  ctypes.byref(y0),
                                                  ctypes.byref(x1),
                                                  ctypes.byref(y1))
            tei.add_segment((x0.value, y0.value, x1.value, y1.value))
        tesseract.TessPageIteratorBoundingBox(it,
                                              RIL_SYMBOL,
                                              ctypes.byref(x0),
                                              ctypes.byref(y0),
                                              ctypes.byref(x1),
                                              ctypes.byref(y1))
        tei.add_graphemes([(None, (x0.value, y0.value, x1.value, y1.value))])
        if not tesseract.TessPageIteratorNext(it, RIL_SYMBOL):
            break
    tesseract.TessPageIteratorDelete(it)
    tesseract.TessBaseAPIEnd(api)
    tesseract.TessBaseAPIDelete(api)
    with open(output_path, 'w') as fp:
        tei.write(fp)
    return storage.get_storage_path(output_path), doc


@app.task(base=NidabaTask, name=u'nidaba.ocr.tesseract')
def ocr_tesseract(doc, method=u'ocr_tesseract', languages=None,
                  extended=False):
    """
    Runs tesseract on an input document.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files
        languages (list): A list of tesseract classifier identifiers
        extended (bool): Switch to enable extended hOCR generation containing
                         character cuts and confidences. Has no effect when
                         direct or legacy implementation is used.

    Returns:
        (unicode, unicode): Storage tuple for the output file
    """
    image_path = storage.get_abs_path(*doc[1])

    # rewrite the segmentation file to lines in UZN format
    seg = TEIFacsimile()
    with storage.StorageFile(*doc[0]) as fp:
        seg.read(fp)
    with storage.StorageFile(doc[1][0], splitext(doc[1][1])[0] + '.uzn', mode='wb') as fp:
        uzn = UZNWriter(fp)
        for line in seg.lines:
            uzn.writerow(*line[:4])

    if isinstance(languages, basestring):
        languages = [languages]
    output_path = storage.insert_suffix(image_path, method, *languages)

    if implementation == 'legacy':
        result_path = output_path + '.html'
        ocr_direct(image_path, output_path, languages)
    elif implementation == 'direct':
        result_path = output_path + '.hocr'
        ocr_direct(image_path, output_path, languages)
    elif implementation == 'capi':
        result_path = output_path + '.xml'
        ocr_capi(image_path, result_path, seg, languages, extended)
    else:
        raise NidabaTesseractException('Invalid implementation selected',
                                       implementation)
    if not result_path[-4:] == '.xml':
        tei = TEIFacsimile()
        with open(result_path) as fp:
            tei.load_hocr(fp)
        os.unlink(result_path)
        with open(output_path + '.xml', 'wb') as fp:
            tei.write(fp)
        result_path = output_path + '.xml'
    return storage.get_storage_path(result_path)


def ocr_capi(image_path, output_path, facsimile, languages, extended=False):
    """
    OCRs an image using the C API provided by tesseract versions 3.02 and
    higher.

    Args:
        image_path (unicode): Path to the input image
        facsimile (nidaba.tei.TEIFacsimile): Facsimile object of the
                                             segmentation
        output_path (unicode): Path to the hOCR output
        languages (list): List of valid tesseract language identifiers
        extended (bool): Switch to select extended hOCR output containing
                         character cuts and confidences values
    """
    # tesseract has a tendency to crash arbitrarily on some inputs
    # necessitating execution in a separate process to ensure the worker
    # doesn't just die. We use fork as the multiprocessing module thinks
    # programmers are too stupid to reap their children.
    # pid = os.fork()
    # if pid != 0:
    #     try:
    #         _, status = os.waitpid(pid, 0)
    #     except OSError as e:
    #         if e.errno not in (errno.EINTR, errno.ECHILD):
    #             raise
    #         return
    #     if os.WIFSIGNALED(status):
    #         raise NidabaTesseractException('Tesseract killed by signal: {0}'.format( os.WTERMSIG(status)))
    #     return

    # ensure we've loaded a tesseract object newer than 3.02
    ver = tesseract.TessVersion()
    if int(ver.split('.')[0]) < 3 or int(ver.split('.')[1]) < 2:
        raise NidabaTesseractException('libtesseract version is too old. Set '
                                       'implementation to direct.')
    api = tesseract.TessBaseAPICreate()
    rc = tesseract.TessBaseAPIInit3(api, tessdata.encode('utf-8'),
                                    ('+'.join(languages)).encode('utf-8'))
    if (rc):
        tesseract.TessBaseAPIDelete(api)
        raise NidabaTesseractException('Tesseract initialization failed.')

    pix = leptonica.pixRead(image_path.encode('utf-8'))
    tesseract.TessBaseAPISetImage2(api, pix)
    if extended:
        # change to single line recognition
        tesseract.TessBaseAPISetPageSegMode(api, 7)
        facsimile.add_respstmt('tesseract', 'character recognition')

        # While tesseract can recognize single words/characters it is extremely
        # slow to do so. We therefore wrote an UZN file containing only lines
        # and clear out segments and graphemes here too.
        facsimile.clear_graphemes()
        facsimile.clear_segments()

        w, h = Image.open(image_path).size
        x0, y0, x1, y1 = (ctypes.c_int(), ctypes.c_int(), ctypes.c_int(),
                          ctypes.c_int())
        for line in facsimile.lines:
            tesseract.TessBaseAPISetRectangle(api, line[0], line[1], line[2] - line[0], line[3] - line[1])
            if tesseract.TessBaseAPIRecognize(api, None):
                leptonica.pixDestroy(ctypes.byref(pix))
                tesseract.TessBaseAPIEnd(api)
                tesseract.TessBaseAPIDelete(api)
                raise NidabaTesseractException('Recognition failed.')
            ri = tesseract.TessBaseAPIGetIterator(api)
            pi = tesseract.TessResultIteratorGetPageIterator(ri)
            facsimile.scope_line(line[4])
            last_word = None
            while True:
                if tesseract.TessPageIteratorIsAtBeginningOf(pi, RIL_WORD):
                    lang = tesseract.TessResultIteratorWordRecognitionLanguage(ri, RIL_WORD).decode('utf-8')
                    tesseract.TessPageIteratorBoundingBox(pi, RIL_WORD,
                                                          ctypes.byref(x0),
                                                          ctypes.byref(y0),
                                                          ctypes.byref(x1),
                                                          ctypes.byref(y1))
                    conf = tesseract.TessResultIteratorConfidence(ri, RIL_WORD)
                    # insert space between word boundaries as they don't get
                    # returned by GetUTF8Text
                    if last_word is not None:
                        facsimile.clear_segment()
                        facsimile.add_graphemes([(u' ', (last_word, 
                                                       y0.value,
                                                       x0.value, 
                                                       y1.value), 100.0)])
                    last_word = x1.value
                    facsimile.add_segment((x0.value, y0.value, x1.value, y1.value),
                                          lang, conf)

                conf = tesseract.TessResultIteratorConfidence(ri, RIL_SYMBOL)
                tesseract.TessPageIteratorBoundingBox(pi, RIL_SYMBOL,
                                                      ctypes.byref(x0),
                                                      ctypes.byref(y0),
                                                      ctypes.byref(x1),
                                                      ctypes.byref(y1))
                grapheme = tesseract.TessResultIteratorGetUTF8Text(ri, RIL_SYMBOL)
                if grapheme is not None:
                    grapheme = grapheme.decode('utf-8')
                facsimile.add_graphemes([(grapheme, (x0.value, y0.value, x1.value,
                                          y1.value), conf)])
                if not tesseract.TessResultIteratorNext(ri, RIL_SYMBOL):
                    break
            # XXX: deleting the page iterator too hangs
            tesseract.TessResultIteratorDelete(ri)
        with open(output_path, 'wb') as fp:
            facsimile.write(fp)
    else:
        tesseract.TessBaseAPISetPageSegMode(api, 4)
        if tesseract.TessBaseAPIRecognize(api, None):
            leptonica.pixDestroy(ctypes.byref(pix))
            tesseract.TessBaseAPIDelete(api)
            raise NidabaTesseractException('Tesseract recognition failed')
        with open(output_path, 'wb') as fp:
            tp = tesseract.TessBaseAPIGetHOCRText(api, 0)
            hocr = StringIO.StringIO()
            hocr.write(ctypes.string_at(tp))
            hocr.seek(0)
            facsimile.load_hocr(hocr)
            facsimile.write(fp)
            tesseract.TessDeleteText(tp)
    tesseract.TessBaseAPIEnd(api)
    tesseract.TessBaseAPIDelete(api)
    #os._exit(os.EX_OK)

def ocr_direct(image_path, output_path, languages):
    """
    OCRs an image by calling the tesseract executable directly. Images are read
    using the linked leptonica library and the given output_path WILL be
    modified by tesseract.

    Args:
        image_path (unicode): Path to the input image
        output_path (unicode): Path to the hOCR output
        languages (list): List of valid tesseract language identifiers
    """
    p = subprocess.Popen(['tesseract', image_path, output_path, '-l',
                          '+'.join(languages), '-psm', '4', '--tessdata-dir',
                          tessdata, 'hocr'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise NidabaTesseractException(err)
