# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile
from lxml import etree
from iris import tesseract

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, 'resources/tesseract'))

class TesseractTests(unittest.TestCase):
    """
    Tests for python tesseract bindings.
    """

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_file_output_png(self):
        """
        Test that tesseract creates hocr output for pngs.
        """
        pngpath = os.path.join(resources, 'image.png')
        outpath = os.path.join(self.tempdir, 'output')
        ocr = tesseract.ocr(pngpath, outpath, ['grc'])
        expected = outpath + '.html'
        self.assertEqual(ocr, expected)
        self.assertTrue(os.path.isfile(expected),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(expected)
        except etree.XMLSyntaxError, e:
            self.fail(msg='The output was not valid html/xml!')


    def test_file_output_tiff(self):
        """
        Test that tesseract creates hocr output for tiffs.
        """
        tiffpath = os.path.join(resources, 'image.tiff')
        outpath = os.path.join(self.tempdir, 'output')
        expected = outpath + '.html'
        ocr = tesseract.ocr(tiffpath, outpath, ['grc'])
        self.assertTrue(os.path.isfile(expected),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(expected)
        except etree.XMLSyntaxError, e:
            self.fail(msg='The output was not valid html/xml!')


    def test_file_output_jpg(self):
        """
        Test that tesseract creates hocr output for jpgs.
        """
        jpgpath = os.path.join(resources, 'image.jpg')
        outpath = os.path.join(self.tempdir, 'output')
        expected = outpath + '.html'

        tesseract.ocr(jpgpath, outpath, ['grc'])
        ocr = self.assertTrue(os.path.isfile(expected),
                        msg='Tesseract did not output a file!')
        try:
            etree.parse(expected)
        except etree.XMLSyntaxError, e:
            self.fail(msg='The output was not valid html/xml!')


    # def test_dir_ocr_inputfail(self):
    #     """
    #     Test that the ocrdir raises the appropriate exception if the
    #     path for the input dir is nonexistent.
    #     """
    #     baddir = os.path.join(resources, 'idontexist')
    #     try:
    #         tesseract.ocrdir(baddir, 'irrelevant', ['grc'])
    #         self.fail()
    #     except Exception as e:
    #         self.assertEqual('Directory did not exist!', str(e))

    # def test_dir_ocr(self):
    #     """
    #     Test that the ocrdir raises the appropriate exception if the
    #     path for the input dir is not a dir.
    #     """
    #     hocr = tesseract.ocrdir(resources, self.tempdir, ['grc'])
    #     self.assertEqual(3, len(hocr))
    #     self.assertEqual(3, len(os.listdir(self.tempdir)))
    #     self.assertIn('image.png.hocr', os.listdir(self.tempdir))
    #     self.assertIn('image.tiff.hocr', os.listdir(self.tempdir))
    #     self.assertIn('image.jpg.hocr', os.listdir(self.tempdir))



if __name__ == '__main__':
    unittest.main()
