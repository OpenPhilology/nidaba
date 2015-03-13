# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile

from lxml import etree
from distutils import spawn
from nose.plugins.skip import SkipTest
from nidaba import ocropus

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, 'resources/ocropus'))


class OcropusTests(unittest.TestCase):

    """
    Tests for python ocropus bindings.
    """

    def setUp(self):
        if None in [spawn.find_executable('ocropus-rpred'),
                    spawn.find_executable('ocropus-gpageseg'),
                    spawn.find_executable('ocropus-hocr')]:
            raise SkipTest

        self.otempdir = unicode(tempfile.mkdtemp())
        # copytree fails if the target directory already exists. Unfortunately
        # not creating the temporary directory using mkstemp() is
        # race-conditiony.
        self.tempdir = os.path.join(self.otempdir, u'stupid')
        shutil.copytree(resources, self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.otempdir)

    def test_file_outpath_png(self):
        """
        Test that ocropus creates hocr outpath for pngs.
        """
        pngpath = os.path.join(self.tempdir, u'image_png.png')
        outpath = os.path.join(self.tempdir, u'outpath_png.hocr')
        modelpath = os.path.join(self.tempdir, u'atriale.pyrnn.gz')
        ocr = ocropus.ocr(pngpath, outpath, modelpath)
        self.assertEqual(ocr, outpath)
        self.assertTrue(os.path.isfile(outpath),
                        msg='Ocropus did not outpath a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')

    def test_file_outpath_tiff(self):
        """
        Test that ocropus creates hocr outpath for tiffs.
        """
        tiffpath = os.path.join(self.tempdir, u'image_tiff.tiff')
        outpath = os.path.join(self.tempdir, u'outpath_tiff.hocr')
        modelpath = os.path.join(self.tempdir, u'atriale.pyrnn.gz')
        ocr = ocropus.ocr(tiffpath, outpath, modelpath)
        self.assertEqual(ocr, outpath)
        self.assertTrue(os.path.isfile(outpath),
                        msg='Ocropus did not outpath a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')

    def test_file_outpath_jpg(self):
        """
        Test that ocropus creates hocr outpath for jpgs.
        """
        jpgpath = os.path.join(self.tempdir, u'image_jpg.jpg')
        outpath = os.path.join(self.tempdir, u'outpath_jpg.hocr')
        modelpath = os.path.join(self.tempdir, u'atriale.pyrnn.gz')
        ocr = ocropus.ocr(jpgpath, outpath, modelpath)
        self.assertEqual(ocr, outpath)
        self.assertTrue(os.path.isfile(outpath),
                        msg='Ocropus did not outpath a file!')
        try:
            etree.parse(outpath)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')


if __name__ == '__main__':
    unittest.main()
