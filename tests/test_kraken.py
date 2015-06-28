# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile
import os

from lxml import etree
from celery import Task
from nose.plugins.skip import SkipTest
from mock import patch, MagicMock

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, 'resources/ocropus'))


class KrakenTests(unittest.TestCase):

    """
    Tests for the kraken plugin.
    """

    def setUp(self):
        config_mock = MagicMock()
        storage_path = unicode(tempfile.mkdtemp())
        config_mock.nidaba_cfg = {
            'storage_path': storage_path,
            'kraken_models': {'default': ('test', 'en-default.hdf5')},
            'ocropus_models': {'ocropus': ('test', 'en-default.pyrnn.gz')},
            'plugins_load': {}
        }

        self.patches = {
            'nidaba.config': config_mock,
        }
        self.patcher = patch.dict('sys.modules', self.patches)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()
	self.storage_path = storage_path
        shutil.copytree(resources, self.storage_path + '/test')
        from nidaba.plugins import kraken
        kraken.setup()
        self.kraken = kraken


    def tearDown(self):
        
        shutil.rmtree(self.storage_path)


    def test_segmentation(self):
        """
        Test that kraken's page segmentation is working
        """
        o = self.kraken.segmentation_kraken.run(('test', 'image_png.png'))
        self.assertTrue(os.path.isfile(os.path.join(self.storage_path, *o[0])),
                        msg='Kraken did not output a file!')


    def test_hdf5_model(self):
        """
        Test that kraken creates hocr output with HDF5 models.
        """
        ocr = self.kraken.ocr_kraken.run((('test', 'image.uzn'), 
                                      ('test', 'image_png.png')), 
                                     model='default')
        try:
            parser = etree.HTMLParser()
            etree.parse(open(os.path.join(self.storage_path, *ocr)), parser)
        except etree.XMLSyntaxError as e:
            print(e.message)
            self.fail(msg='The outpath was not valid html/xml!')


    def test_file_outpath_png(self):
        """
        Test that kraken creates hocr output for pngs.
        """
        ocr = self.kraken.ocr_kraken.run((('test', 'image.uzn'), 
                                      ('test', 'image_png.png')), 
                                     model='ocropus')
        try:
            parser = etree.HTMLParser()
            etree.parse(open(os.path.join(self.storage_path, *ocr)), parser)
        except etree.XMLSyntaxError as e:
            print(e.message)
            self.fail(msg='The outpath was not valid html/xml!')

    def test_file_outpath_tiff(self):
        """
        Test that kraken creates hocr output for tiffs.
        """
        ocr = self.kraken.ocr_kraken.run((('test', 'image.uzn'), 
                                      ('test', 'image_tiff.tiff')), 
                                     model='ocropus')
        try:
            parser = etree.HTMLParser()
            etree.parse(open(os.path.join(self.storage_path, *ocr)), parser)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')


    def test_file_outpath_jpg(self):
        """
        Test that kraken creates hocr output for jpgs.
        """
        ocr = self.kraken.ocr_kraken.run((('test', 'image.uzn'), 
                                      ('test', 'image_jpg.jpg')), 
                                     model='ocropus')
        try:
            parser = etree.HTMLParser()
            etree.parse(open(os.path.join(self.storage_path, *ocr)), parser)
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid html/xml!')


    def test_nlbin(self):
        """
        Test that kraken's nlbin is callable.
        """
        ret = self.kraken.nlbin.run(('test', 'image_jpg.jpg'))
        self.assertTrue(os.path.isfile(os.path.join(self.storage_path, *ret)),
                        msg='Kraken did not output a file!')


if __name__ == '__main__':
    unittest.main()
