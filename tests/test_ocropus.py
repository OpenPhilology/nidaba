# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile
import os

from lxml import etree
from distutils import spawn
from nose.plugins.skip import SkipTest
from mock import patch, MagicMock

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

        self.config_mock = MagicMock()
        self.config_mock.nidaba.config.everything.log.return_value = True
        modules = {
            'nidaba.config': self.config_mock.config
        }
        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        from nidaba.plugins import ocropus
        self.ocropus = ocropus

        self.otempdir = unicode(tempfile.mkdtemp())
        # copytree fails if the target directory already exists. Unfortunately
        # not creating the temporary directory using mkstemp() is
        # race-conditiony.
        self.tempdir = os.path.join(self.otempdir, u'stupid')
        shutil.copytree(resources, self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.otempdir)

    def test_file_path_correct(self):
        """
        Test that output is placed in the correct directory.
        """
        pngpath = os.path.join(self.tempdir, u'image_png.png')
        wd = tempfile.mkdtemp()
        swd = tempfile.mkdtemp()

        outpath = os.path.join(swd, u'outpath_png.hocr')
        os.chdir(wd)

        modelpath = os.path.join(self.tempdir, u'en-default.pyrnn.gz')
        ocr = self.ocropus.ocr(pngpath, outpath, modelpath)
        self.assertTrue(os.path.isfile(ocr),
                        msg='Ocropus did not outpath a file!')
        self.assertEqual(os.path.dirname(ocr), swd,
                         msg='Output not placed in correct directory')
        try:
            etree.parse(ocr)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')
        finally:
            shutil.rmtree(swd)
            shutil.rmtree(wd)

    def test_file_outpath_png(self):
        """
        Test that ocropus creates hocr output for pngs.
        """
        pngpath = os.path.join(self.tempdir, u'image_png.png')
        outpath = os.path.join(self.tempdir, u'outpath_png.hocr')
        modelpath = os.path.join(self.tempdir, u'en-default.pyrnn.gz')
        ocr = self.ocropus.ocr(pngpath, outpath, modelpath)
        self.assertTrue(os.path.isfile(ocr),
                        msg='Ocropus did not outpath a file!')
        try:
            etree.parse(ocr)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')

    def test_file_outpath_tiff(self):
        """
        Test that ocropus creates hocr output for tiffs.
        """
        tiffpath = os.path.join(self.tempdir, u'image_tiff.tiff')
        outpath = os.path.join(self.tempdir, u'outpath_tiff.hocr')
        modelpath = os.path.join(self.tempdir, u'en-default.pyrnn.gz')
        ocr = self.ocropus.ocr(tiffpath, outpath, modelpath)
        self.assertTrue(os.path.isfile(ocr),
                        msg='Ocropus did not output a file!')
        try:
            etree.parse(ocr)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')

    def test_file_outpath_jpg(self):
        """
        Test that ocropus creates hocr output for jpgs.
        """
        jpgpath = os.path.join(self.tempdir, u'image_jpg.jpg')
        outpath = os.path.join(self.tempdir, u'outpath_jpg.hocr')
        modelpath = os.path.join(self.tempdir, u'en-default.pyrnn.gz')
        ocr = self.ocropus.ocr(jpgpath, outpath, modelpath)
        self.assertTrue(os.path.isfile(ocr),
                        msg='Ocropus did not output a file!')
        try:
            etree.parse(ocr)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')


if __name__ == '__main__':
    unittest.main()
