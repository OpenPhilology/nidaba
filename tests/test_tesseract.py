# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import os
import shutil
import tempfile
import ctypes

from lxml import etree
from distutils import spawn
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
            'lang_dicts': {},
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
            raise unittest.SkipTest
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.tiff')),
                                           languages=['grc', 'eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            doc = etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_direct_multiple(self):
        """
        Test that direct tesseract calls create hocr output for multiple
        languages.
        """
        if not spawn.find_executable('tesseract'):
            raise unittest.SkipTest

        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.tiff')),
                                           languages=['grc', 'eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
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
            raise unittest.SkipTest
        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.tiff')),
                                           languages=['eng'],
                                           extended=True)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')

        try:
            h = etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')
        self.assertIsNotNone(h.findall(".//line"), msg='Tesseract did not write lines.')
        self.assertIsNotNone(h.findall(".//seg"), msg='Tesseract did not write segments.')
        self.assertIsNotNone(h.findall(".//g"), msg='Tesseract did not write graphemes.')


    def test_capi_file_output_png(self):
        """
        Test that tesseract CAPI calls create hocr output for pngs.
        """

        try:
            t = ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise unittest.SkipTest

        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.png')),
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_capi_file_output_tiff(self):
        """
        Test that tesseract CAPI calls create hocr output for tiffs.
        """
        try:
            t = ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise unittest.SkipTest

        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.tiff')),
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_capi_file_output_jpg(self):
        """
        Test that tesseract CAPI calls create hocr output for jpgs.
        """

        try:
            t = ctypes.cdll.LoadLibrary('libtesseract.so.3')
        except:
            raise unittest.SkipTest

        self.tesseract.setup(tessdata=tessdata, implementation='capi')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.jpg')),
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_direct_file_output_png(self):
        """
        Test that direct tesseract calls create hocr output for pngs.
        """

        if not spawn.find_executable('tesseract'):
            raise unittest.SkipTest

        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.png')),
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_direct_file_output_tiff(self):
        """
        Test that direct tesseract calls create hocr output for tiffs.
        """
        if not spawn.find_executable('tesseract'):
            raise unittest.SkipTest

        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.tiff')),
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


    def test_direct_file_output_jpg(self):
        """
        Test that direct tesseract calls create hocr output for jpgs.
        """
        if not spawn.find_executable('tesseract'):
            raise unittest.SkipTest

        self.tesseract.setup(tessdata=tessdata, implementation='direct')
        ocr = self.tesseract.ocr_tesseract.run((('test', 'segmentation.xml'), ('test',
                                           'image.jpg')),
                                           languages=['eng'],
                                           extended=False)
        outpath = os.path.join(self.storage_path, *ocr)
        self.assertTrue(os.path.isfile(outpath), msg='Tesseract did not '
                        'output a file!')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


if __name__ == '__main__':
    unittest.main()
