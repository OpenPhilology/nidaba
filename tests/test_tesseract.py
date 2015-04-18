# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile
import subprocess

from lxml import etree
from nidaba.plugins import tesseract
from distutils import spawn
from nose.plugins.skip import SkipTest

thisfile = os.path.abspath(os.path.dirname(__file__))
tessdata = os.path.abspath(os.path.join(thisfile, 'resources'))


class TesseractTests(unittest.TestCase):

    """
    Tests the tesseract plugin.
    """

    def setUp(self):
        if not spawn.find_executable('tesseract'):
            raise SkipTest

        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_capi_file_output_png(self):
        """
        Test that tesseract CAPI calls create hocr output for pngs.
        """
        pngpath = os.path.join(tessdata, 'image.png')
        outpath = os.path.join(self.tempdir, 'output')
        tesseract.setup({'tessdata': tessdata, 'implementation': 'capi'})
        tesseract.ocr_capi(pngpath, outpath, ['grc'])
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')

    def test_capi_file_output_tiff(self):
        """
        Test that tesseract CAPI calls create hocr output for tiffs.
        """
        tiffpath = os.path.join(tessdata, 'image.tiff')
        outpath = os.path.join(self.tempdir, 'output')
        tesseract.setup({'tessdata': tessdata, 'implementation': 'capi'})
        tesseract.ocr_capi(tiffpath, outpath, ['grc'])
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')

    def test_capi_file_output_jpg(self):
        """
        Test that tesseract CAPI calls create hocr output for jpgs.
        """
        jpgpath = os.path.join(tessdata, 'image.jpg')
        outpath = os.path.join(self.tempdir, 'output')
        tesseract.setup({'tessdata': tessdata, 'implementation': 'capi'})
        tesseract.ocr_capi(jpgpath, outpath, ['grc'])
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')

    def test_direct_file_output_png(self):
        """
        Test that direct tesseract calls create hocr output for pngs.
        """
        pngpath = os.path.join(tessdata, 'image.png')
        outpath = os.path.join(self.tempdir, 'output')
        tesseract.setup({'tessdata': tessdata, 'implementation': 'direct'})
        tesseract.ocr_direct(pngpath, outpath, ['grc'])
        if os.path.isfile(outpath + '.html'):
            outpath = outpath + '.html'
        else:
            outpath = outpath + '.hocr'
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')

    def test_direct_file_output_tiff(self):
        """
        Test that direct tesseract create hocr output for tiffs.
        """
        tiffpath = os.path.join(tessdata, 'image.tiff')
        outpath = os.path.join(self.tempdir, 'output')
        tesseract.setup({'tessdata': tessdata, 'implementation': 'direct'})
        tesseract.ocr_direct(tiffpath, outpath, ['grc'])
        if os.path.isfile(outpath + '.html'):
            outpath = outpath + '.html'
        else:
            outpath = outpath + '.hocr'
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')

    def test_direct_file_output_jpg(self):
        """
        Test that direct tesseract calls create hocr output for jpgs.
        """
        jpgpath = os.path.join(tessdata, 'image.jpg')
        outpath = os.path.join(self.tempdir, 'output')
        tesseract.setup({'tessdata': tessdata, 'implementation': 'direct'})
        tesseract.ocr_direct(jpgpath, outpath, ['grc'])
        if os.path.isfile(outpath + '.html'):
            outpath = outpath + '.html'
        else:
            outpath = outpath + '.hocr'
        self.assertTrue(os.path.isfile(outpath),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


if __name__ == '__main__':
    unittest.main()
