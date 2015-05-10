# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile
import os

from lxml import etree
from nose.plugins.skip import SkipTest
from mock import patch, MagicMock

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, 'resources/ocropus'))


class KrakenTests(unittest.TestCase):

    """
    Tests for python ocropus bindings.
    """

    def setUp(self):
        try:
            self.config_mock = MagicMock()
            self.config_mock.nidaba.config.everything.log.return_value = True
            modules = {
                'nidaba.config': self.config_mock.config
            }
            self.module_patcher = patch.dict('sys.modules', modules)
            self.module_patcher.start()
            from nidaba.plugins import kraken
            kraken.setup()
            self.kraken = kraken
            self.tempdir = unicode(tempfile.mkdtemp())
        except:
            raise SkipTest

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_file_outpath_png(self):
        """
        Test that kraken creates hocr output for pngs.
        """
        pngpath = os.path.join(resources, u'image_png.png')
        modelpath = os.path.join(resources, u'en-default.pyrnn.gz')
        ocr = self.kraken.ocr(pngpath, modelpath)
        try:
            parser = etree.HTMLParser()
            etree.fromstring(ocr, parser)
        except etree.XMLSyntaxError as e:
            print(e.message)
            self.fail(msg='The outpath was not valid html/xml!')

    def test_file_outpath_tiff(self):
        """
        Test that kraken creates hocr output for tiffs.
        """
        tiffpath = os.path.join(resources, u'image_tiff.tiff')
        modelpath = os.path.join(resources, u'en-default.pyrnn.gz')
        ocr = self.kraken.ocr(tiffpath, modelpath)
        try:
            parser = etree.HTMLParser()
            etree.fromstring(ocr, parser)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')

    def test_file_outpath_jpg(self):
        """
        Test that kraken creates hocr output for jpgs.
        """
        jpgpath = os.path.join(resources, u'image_jpg.jpg')
        modelpath = os.path.join(resources, u'en-default.pyrnn.gz')
        ocr = self.kraken.ocr(jpgpath, modelpath)
        try:
            parser = etree.HTMLParser()
            etree.fromstring(ocr, parser)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')

    def test_nlbin(self):
        """
        Test that kraken's nlbin is callable.
        """
        jpgpath = os.path.join(resources, u'image_jpg.jpg')
        outpath = os.path.join(self.tempdir, u'output.png')
        self.kraken.kraken_nlbin(jpgpath, outpath)
        self.assertTrue(os.path.isfile(outpath),
                        msg='Kraken did not output a file!')


if __name__ == '__main__':
    unittest.main()
