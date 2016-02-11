# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
import os
import shutil
import tempfile

from lxml import etree
from mock import patch, MagicMock

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, 'resources/ocropus'))


class KrakenTests(unittest.TestCase):

    """
    Tests for the kraken plugin.
    """

    def setUp(self):
        try:
            self.config_mock = MagicMock()
            storage_path = unicode(tempfile.mkdtemp())
            self.config_mock.nidaba_cfg = { 
                'storage_path': storage_path,
                'lang_dicts': {},
                'kraken_models': {'default': ('test', 'en-default.hdf5')},
                'ocropus_models': {'ocropus': ('test', 'en-default.pyrnn.gz')},
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
            shutil.copytree(resources, self.storage_path + '/test')
            from nidaba.plugins import kraken
            kraken.setup()
            self.kraken = kraken
        except:
            raise unittest.SkipTest

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.storage_path)

    def test_segmentation(self):
        """
        Test that kraken's page segmentation is working
        """
        o = self.kraken.segmentation_kraken.run(('test', 'image_png.png'))
        self.assertTrue(os.path.isfile(os.path.join(self.storage_path, *o[0])),
                        msg='Kraken did not output a file!')
        try:
            etree.parse(open(os.path.join(self.storage_path, *o[0])))
        except etree.XMLSyntaxError as e:
            print(e.message)
            self.fail(msg='The outpath was not valid xml!')
        except IOError:
            self.fail('Kraken did not output a file!')

    def test_file_outpath_png(self):
        """
        Test that kraken creates TEI output for pngs.
        """
        ocr = self.kraken.ocr_kraken.run((('test', 'segmentation.xml'), 
                                      ('test', 'image_png.png')), 
                                     model='ocropus')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError as e:
            print(e.message)
            self.fail(msg='The outpath was not valid xml!')
        except IOError:
            self.fail('Kraken did not output a file!')

    def test_file_outpath_tiff(self):
        """
        Test that kraken creates hocr output for tiffs.
        """
        ocr = self.kraken.ocr_kraken.run((('test', 'segmentation.xml'), 
                                      ('test', 'image_tiff.tiff')), 
                                     model='ocropus')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid xml!')
        except IOError:
            self.fail('Kraken did not output a file!')


    def test_file_outpath_jpg(self):
        """
        Test that kraken creates hocr output for jpgs.
        """
        ocr = self.kraken.ocr_kraken.run((('test', 'segmentation.xml'), 
                                      ('test', 'image_jpg.jpg')), 
                                     model='ocropus')
        try:
            etree.parse(open(os.path.join(self.storage_path, *ocr)))
        except etree.XMLSyntaxError:
            self.fail(msg='The outpath was not valid xml!')
        except IOError:
            self.fail('Kraken did not output a file!')


    def test_nlbin(self):
        """
        Test that kraken's nlbin is callable.
        """
        ret = self.kraken.nlbin.run(('test', 'image_jpg.jpg'))
        self.assertTrue(os.path.isfile(os.path.join(self.storage_path, *ret)),
                        msg='Kraken did not output a file!')


if __name__ == '__main__':
    unittest.main()
