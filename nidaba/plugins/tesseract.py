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

from __future__ import absolute_import

import subprocess
import ctypes
import dominate

from PIL import Image
from distutils import spawn
from dominate.tags import div, span, meta, br

from nidaba import storage
from nidaba.celery import app
from nidaba.tasks.helper import NidabaTask
from nidaba.nidabaexceptions import NidabaTesseractException
from nidaba.nidabaexceptions import NidabaPluginException


implementation = u'capi'
tessdata = u'/usr/share/tesseract-ocr/'


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
            ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise NidabaPluginException('Loading libtesseract failed.')


class micro_hocr(object):
    """
    A simple class encapsulating hOCR attributes
    """
    def __init__(self):
        self.output = u''

    def __str__(self):
        return self.output

    def add(self, *args):
        if self.output:
            self.output += u'; '
        for arg in args:
            if isinstance(arg, basestring):
                self.output += arg + ' '
            elif isinstance(arg, tuple):
                self.output += u','.join([unicode(v) for v in arg]) + u' '
            else:
                self.output += unicode(arg) + u' '
        self.output = self.output.strip()


@app.task(base=NidabaTask, name=u'nidaba.ocr.tesseract')
def ocr_tesseract(doc, method=u'ocr_tesseract', languages=None, extended=True):
    """
    Runs tesseract on an input document.

    Args:
        doc (unicode, unicode): The input document tuple
        method (unicode): The suffix string appended to all output files
                          languages (list of unicode): A list of languages for
                          the tesseract language model
        languages (list): A list of tesseract classifier identifiers
        extended (bool): Switch to enable extended hOCR generation containing
                         character cuts and confidences. Has no effect when
                         direct or legacy implementation is used.

    Returns:
        (unicode, unicode): Storage tuple for the output file
    """
    image_path = storage.get_abs_path(*doc)
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
        result_path = output_path + '.hocr'
        ocr_capi(image_path, result_path, languages, extended)
    else:
        raise NidabaTesseractException('Invalid implementation selected',
                                       implementation)
    return storage.get_storage_path(result_path)



def delta(root=(0, 0, 0, 0), coordinates=None):
    """Calculates the running delta from a root coordinate according to the
    hOCR standard.

    It uses a root bounding box (x0, y0, x1, y1) and calculates the delta from
    the points (min(x0, x1), min(y0, y1)) and (min(x0, x1), max(y0, y1)) for
    the first and second pair of values in a delta (dx0, dy0, dx1, dy1)
    respectively.

    Args:
        coordinates (list): List of tuples of length 4 containing absolute
                            coordinates for character bounding boxes.

    Returns:
        A tuple dx0, dy0, dx1, dy1
    """
    for box in coordinates:
        yield (min(box[0], box[2]) - min(root[0], root[2]),
               min(box[1], box[3]) - min(root[1], root[3]),
               max(box[0], box[2]) - min(root[0], root[2]),
               max(box[1], box[3]) - max(root[1], root[3]))
        root = box


def ocr_capi(image_path, output_path, languages, extended=True):
    """
    OCRs an image using the C API provided by tesseract versions 3.02 and
    higher. Images are read using pillow allowing a wider range of formats than
    leptonica and results are written to a fixed output document.

    Args:
        image_path (unicode): Path to the input image
        output_path (unicode): Path to the hOCR output
        languages (list): List of valid tesseract language identifiers
        extended (bool): Switch to select extended hOCR output containing
                         character cuts and confidences values.
    """

    img = Image.open(image_path)
    w, h = img.size

    # There is a regression in TessBaseAPISetImage somewhere between 3.02 and
    # 3.03. Unfortunately the tesseract maintainers close all bug reports
    # concerning their API, so we just convert to grayscale here.
    img = img.convert('L')
    try:
        tesseract = ctypes.cdll.LoadLibrary('libtesseract.so.3')
    except OSError as e:
        raise NidabaTesseractException('Loading libtesseract failed: ' +
                                       e.message)

    # set up all return types
    tesseract.TessVersion.restype = ctypes.c_char_p
    tesseract.TessResultIteratorConfidence.restype = ctypes.c_float
    tesseract.TessResultIteratorWordRecognitionLanguage.restype = ctypes.c_char_p
    tesseract.TessResultIteratorGetUTF8Text.restype = ctypes.c_char_p

    # ensure we've loaded a tesseract object newer than 3.02
    ver = tesseract.TessVersion()
    if int(ver.split('.')[0]) < 3 or int(ver.split('.')[1]) < 2:
        raise NidabaTesseractException('libtesseract version is too old. Set'
                                       'implementation to direct.')
    api = tesseract.TessBaseAPICreate()
    rc = tesseract.TessBaseAPIInit3(api, str(tessdata),
                                    ('+'.join(languages)).encode('utf-8'))
    if (rc):
        tesseract.TessBaseAPIDelete(api)
        raise NidabaTesseractException('Tesseract initialization failed.')
    tesseract.TessBaseAPISetImage(api, ctypes.c_char_p(str(img.tobytes())), w,
                                  h, 1, w)
    if tesseract.TessBaseAPIRecognize(api, None):
        tesseract.TessBaseAPIDelete(api)
        raise NidabaTesseractException('Tesseract recognition failed')
    if extended:
        ri = tesseract.TessBaseAPIGetIterator(api)
        pi = tesseract.TessResultIteratorGetPageIterator(ri)
        doc = dominate.document()

        (RIL_BLOCK, RIL_PARA, RIL_TEXTLINE,
         RIL_WORD, RIL_SYMBOL) = map(ctypes.c_int, xrange(5))

        with doc.head:
            meta(name='ocr-system', content='tesseract')
            meta(name='ocr-capabilities', content='ocr_page ocr_carea '
                 'ocr_line ocrx_word')
            meta(charset='utf-8')

        hocr_title = micro_hocr()
        hocr_title.add(u'bbox', 0, 0, str(w), str(h))
        hocr_title.add(u'image', image_path)

        with doc.add(div(cls='ocr_page', title=str(hocr_title))):
            confidences = []
            c_boxes = None
            while True:
                x0, y0, x1, y1 = (ctypes.c_int(), ctypes.c_int(), ctypes.c_int(),
                                  ctypes.c_int())
                if tesseract.TessPageIteratorIsAtBeginningOf(pi, RIL_BLOCK):
                    block_div = div(cls='ocr_carea')
                    tesseract.TessPageIteratorBoundingBox(pi, RIL_BLOCK,
                                                          ctypes.byref(x0),
                                                          ctypes.byref(y0),
                                                          ctypes.byref(x1),
                                                          ctypes.byref(y1))
                    block_title = micro_hocr()
                    block_title.add(u'bbox', x0.value, y0.value, x1.value,
                                    y1.value)
                    block_div['title'] = str(block_title)
                if tesseract.TessPageIteratorIsAtBeginningOf(pi, RIL_TEXTLINE):
                    if c_boxes:
                        line_title.add('cuts', *list(delta(l_box, c_boxes)))
                        line_span['title'] = str(line_title)
                    c_boxes = []
                    line_span = span(cls='ocr_line')
                    tesseract.TessPageIteratorBoundingBox(pi, RIL_TEXTLINE,
                                                          ctypes.byref(x0),
                                                          ctypes.byref(y0),
                                                          ctypes.byref(x1),
                                                          ctypes.byref(y1))
                    line_title = micro_hocr()
                    l_box = (x0.value, y0.value, x1.value, y1.value)
                    line_title.add(u'bbox', *l_box)
                    block_div.add(line_span)
                    block_div.add(br())
                if tesseract.TessPageIteratorIsAtBeginningOf(pi, RIL_WORD):
                    if confidences:
                        word_title.add('x_conf', *[str(int(v)) for v in confidences])
                        word_span['title'] = str(word_title)
                        confidences = []
                    word_span = span(cls='ocrx_word')
                    line_span.add(word_span)
                    lang = tesseract.TessResultIteratorWordRecognitionLanguage(ri, RIL_WORD).decode('utf-8')
                    word_span['lang'] = lang
                    tesseract.TessPageIteratorBoundingBox(pi, RIL_WORD,
                                                          ctypes.byref(x0),
                                                          ctypes.byref(y0),
                                                          ctypes.byref(x1),
                                                          ctypes.byref(y1))
                    word_title = micro_hocr()
                    word_title.add(u'bbox', x0.value, y0.value, x1.value,
                                   y1.value)
                    word_span.add(tesseract.TessResultIteratorGetUTF8Text(ri, RIL_WORD).decode('utf-8'))
                # then the confidence value
                confidences.append(tesseract.TessResultIteratorConfidence(ri,
                                                                          RIL_SYMBOL))
                tesseract.TessPageIteratorBoundingBox(pi, RIL_WORD,
                                                      ctypes.byref(x0),
                                                      ctypes.byref(y0),
                                                      ctypes.byref(x1),
                                                      ctypes.byref(y1))
                c_boxes.append((x0.value, y0.value, x1.value, y1.value))
                if tesseract.TessResultIteratorNext(ri, RIL_SYMBOL) == 0:
                    if c_boxes:
                        line_title.add('cuts', *list(delta(l_box, c_boxes)))
                        line_span['title'] = str(line_title)
                    if confidences:
                        word_title.add('x_conf', *[str(int(v)) for v in confidences])
                        word_span['title'] = str(word_title)
                    break
        with open(output_path, 'wb') as fp:
            fp.write(unicode(doc).encode('utf-8'))
    else:
        with open(output_path, 'wb') as fp:
            tp = tesseract.TessBaseAPIGetHOCRText(api)
            fp.write(ctypes.string_at(tp))
            tesseract.TessDeleteText(tp)
    tesseract.TessBaseAPIDelete(api)


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
                          '+'.join(languages), '--tessdata-dir', tessdata,
                          'hocr'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise NidabaTesseractException(err)
