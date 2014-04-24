# -*- coding: utf-8 -*-
import unittest
import os
import tempfile as t
import tesseract
import glob
from lxml import etree

resources = os.path.abspath('tests/resources/tesseract')

class TesseractTests(unittest.TestCase):
    """Tests for python tesseract bindings."""

    def test_file_output_png(self):
        """Test that tesseract creates hocr output for pngs."""
        tempdir = t.mkdtemp()
        pngpath = os.path.join(resources, 'image.png')
        outpath = os.path.join(tempdir, 'output.hocr')
        expected = outpath + '.html'
        tesseract.ocr(pngpath, outpath, 'grc')
        self.assertTrue(os.path.isfile(expected),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(expected)
        except etree.XMLSyntaxError, e:
            self.fail(msg='The output was not valid html/xml!')


    def test_file_output_tiff(self):
        """Test that tesseract creates hocr output for tiffs."""
        tempdir = t.mkdtemp()
        tiffpath = os.path.join(resources, 'image.tiff')
        outpath = os.path.join(tempdir, 'output.hocr')
        expected = outpath + '.html'
        tesseract.ocr(tiffpath, outpath, 'grc')
        self.assertTrue(os.path.isfile(expected),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(expected)
        except etree.XMLSyntaxError, e:
            self.fail(msg='The output was not valid html/xml!')


    def test_file_output_jpg(self):
        """Test that tesseract creates hocr output for jpgs."""
        tempdir = t.mkdtemp()
        jpgpath = os.path.join(resources, 'image.jpg')
        outpath = os.path.join(tempdir, 'output.hocr')
        expected = outpath + '.html'
        tesseract.ocr(jpgpath, outpath, 'grc')
        self.assertTrue(os.path.isfile(expected),
                        msg='Tesseract did not output a file!')

        try:
            etree.parse(expected)
        except etree.XMLSyntaxError, e:
            self.fail(msg='The output was not valid html/xml!')


if __name__ == '__main__':
    unittest.main()