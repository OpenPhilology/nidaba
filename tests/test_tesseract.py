# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import os
import shutil
import tempfile
import ctypes

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
        self.config_mock = MagicMock()
        storage_path = unicode(tempfile.mkdtemp())
        self.config_mock.nidaba_cfg = {
            'storage_path': storage_path,
            'plugins_load': {}
        }

        self.patches = {
            'nidaba.config': self.config_mock,
        }
        self.patcher = patch.dict('sys.modules', self.patches)
        self.patcher2 = patch('nidaba.storage.nidaba_cfg', self.config_mock.nidaba_cfg)
        self.addCleanup(self.patcher2.stop)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()
        self.patcher2.start()
	self.storage_path = storage_path
        shutil.copytree(tessdata, self.storage_path + '/test')
        from nidaba.plugins import tesseract
        self.tesseract = tesseract
        

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.storage_path)

    def test_capi_multiple(self):
        """
        Test that tesseract CAPI calls create hocr output for multiple
        languages.
        """
        try:
            t = ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise SkipTest
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.tiff'), ('test',
                                           'image.uzn')), 
                                           languages=['grc', 'eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
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

        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.tiff'), ('test',
                                           'image.uzn')), 
                                           languages=['grc', 'eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
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
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.tiff'), ('test',
                                           'image.uzn')), 
                                           languages=['eng'],
                                           extended=True)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')

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

        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.png'), ('test',
                                           'image.uzn')), 
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
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

        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.tiff'), ('test',
                                           'image.uzn')), 
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
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

        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.jpg'), ('test',
                                           'image.uzn')), 
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
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

        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.png'), ('test',
                                           'image.uzn')), 
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
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

        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.tiff'), ('test',
                                           'image.uzn')), 
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
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

        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'image.jpg'), ('test',
                                           'image.uzn')), 
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            html.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


if __name__ == '__main__':
    unittest.main()
