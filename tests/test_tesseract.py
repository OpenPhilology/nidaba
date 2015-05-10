# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile
import subprocess
import ctypes
import unicodedata

from lxml import html, etree
from distutils import spawn
from nose.plugins.skip import SkipTest
from mock import patch, MagicMock

thisfile = os.path.abspath(os.path.dirname(__file__))
tessdata = os.path.abspath(os.path.join(thisfile, 'resources'))


class TesseractTests(unittest.TestCase):

    """
    Tests the tesseract plugin.
    """

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.config_mock = MagicMock()
        self.config_mock.nidaba.config.everything.log.return_value = True
        modules = {
            'nidaba.config': self.config_mock.config
        }
        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        from nidaba.plugins import tesseract
        self.tesseract = tesseract
        

    def tearDown(self):
        shutil.rmtree(self.tempdir)


    def test_capi_multiple(self):
        """
        Test that tesseract CAPI calls create hocr output for multiple
        languages.
        """
        try:
            t = ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise SkipTest

        tiffpath = os.path.join(tessdata, 'image.tiff')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        self.tesseract.ocr_capi(tiffpath, outpath, ['grc', 'eng'])
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_direct_multiple(self):
        """
        Test that direct tesseract calls create hocr output for multiple
        languages.
        """
        if not spawn.find_executable('tesseract'):
            raise SkipTest

        tiffpath = os.path.join(tessdata, 'image.tiff')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        self.tesseract.ocr_direct(tiffpath, outpath, ['grc', 'eng'])
        if os.path.isfile(outpath + '.html'):
            outpath = outpath + '.html'
        else:
            outpath = outpath + '.hocr'
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_capi_extended(self):
        """
        Test that the CAPI extended output contains character cuts in each
        ocr_line and character confidences in each ocrx_word.
        """

        try:
            ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise SkipTest

        pngpath = os.path.join(tessdata, 'image.png')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        self.tesseract.ocr_capi(pngpath, outpath, ['grc'], extended=True)
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            h = html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')
        lines = h.findall(".//span[@class='ocr_line']")
        words = h.findall(".//span[@class='ocrx_word']")
        for line in lines:
            self.assertIn('cuts', line.get('title'), 'ocr_Line without '
                          'character cuts')
        for word in words:
            title = word.get('title')
            fields = [field.strip() for field in title.split(';')]
            conf = [b for b in fields if b.startswith('x_conf')]
            self.assertEqual(len(conf), 1, 'ocrx_word contains more than one '
                             'x_conf field')
            # As one grapheme (visual character) is not always equal to one
            # codepoint it only makes sense to test that there are less
            # confidence value than codepoints.
            self.assertLess(len(conf[0].split()), word.text,
                             'ocrx_word contains incorrect number of '
                             'character confidences')


    def test_capi_file_output_png(self):
        """
        Test that tesseract CAPI calls create hocr output for pngs.
        """

        try:
            t = ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise SkipTest

        pngpath = os.path.join(tessdata, 'image.png')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        self.tesseract.ocr_capi(pngpath, outpath, ['grc'])
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_capi_file_output_tiff(self):
        """
        Test that tesseract CAPI calls create hocr output for tiffs.
        """
        try:
            t = ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise SkipTest

        tiffpath = os.path.join(tessdata, 'image.tiff')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        self.tesseract.ocr_capi(tiffpath, outpath, ['grc'])
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_capi_file_output_jpg(self):
        """
        Test that tesseract CAPI calls create hocr output for jpgs.
        """

        try:
            t = ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise SkipTest

        jpgpath = os.path.join(tessdata, 'image.jpg')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        self.tesseract.ocr_capi(jpgpath, outpath, ['grc'])
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_direct_file_output_png(self):
        """
        Test that direct tesseract calls create hocr output for pngs.
        """

        if not spawn.find_executable('tesseract'):
            raise SkipTest

        pngpath = os.path.join(tessdata, 'image.png')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        self.tesseract.ocr_direct(pngpath, outpath, ['grc'])
        if os.path.isfile(outpath + '.html'):
            outpath = outpath + '.html'
        else:
            outpath = outpath + '.hocr'
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_direct_file_output_tiff(self):
        """
        Test that direct tesseract calls create hocr output for tiffs.
        """
        if not spawn.find_executable('tesseract'):
            raise SkipTest

        tiffpath = os.path.join(tessdata, 'image.tiff')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        self.tesseract.ocr_direct(tiffpath, outpath, ['grc'])
        if os.path.isfile(outpath + '.html'):
            outpath = outpath + '.html'
        else:
            outpath = outpath + '.hocr'
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_direct_file_output_jpg(self):
        """
        Test that direct tesseract calls create hocr output for jpgs.
        """
        if not spawn.find_executable('tesseract'):
            raise SkipTest

        jpgpath = os.path.join(tessdata, 'image.jpg')
        outpath = os.path.join(self.tempdir, 'output')
        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        self.tesseract.ocr_direct(jpgpath, outpath, ['grc'])
        if os.path.isfile(outpath + '.html'):
            outpath = outpath + '.html'
        else:
            outpath = outpath + '.hocr'
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


if __name__ == '__main__':
    unittest.main()
