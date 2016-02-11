# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile
import os

from lxml import etree
from distutils import spawn
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
            raise unittest.SkipTest
        self.config_mock = MagicMock()
        storage_path = unicode(tempfile.mkdtemp())
        self.config_mock.nidaba_cfg = {
            'storage_path': storage_path,
            'lang_dicts': {},
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
        from nidaba.plugins import ocropus
        ocropus.setup()
        self.ocropus = ocropus


    def tearDown(self):
        shutil.rmtree(self.storage_path)

    def test_file_path_correct(self):
        """
        Test that output is placed in the correct directory.
        """
        ocr = self.ocropus.ocr_ocropus.run((('test', 'segmentation.xml'),
                                            ('test', 'image_png.png')),
                                           model='ocropus')
        try:
            parser = etree.HTMLParser()
            etree.parse(open(os.path.join(self.storage_path, *ocr)), parser)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')

    def test_file_outpath_png(self):
        """
        Test that ocropus creates hocr output for pngs.
        """
        ocr = self.ocropus.ocr_ocropus.run((('test', 'segmentation.xml'),
                                            ('test', 'image_png.png')),
                                           model='ocropus')
        try:
            parser = etree.HTMLParser()
            etree.parse(open(os.path.join(self.storage_path, *ocr)), parser)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')

    def test_file_outpath_tiff(self):
        """
        Test that ocropus creates hocr output for tiffs.
        """
        ocr = self.ocropus.ocr_ocropus.run((('test', 'segmentation.xml'),
                                            ('test', 'image_tiff.tiff')),
                                           model='ocropus')
        try:
            parser = etree.HTMLParser()
            etree.parse(open(os.path.join(self.storage_path, *ocr)), parser)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')

    def test_file_outpath_jpg(self):
        """
        Test that ocropus creates hocr output for jpgs.
        """
        ocr = self.ocropus.ocr_ocropus.run((('test', 'segmentation.xml'),
                                            ('test', 'image_jpg.jpg')),
                                           model='ocropus')
        try:
            parser = etree.HTMLParser()
            etree.parse(open(os.path.join(self.storage_path, *ocr)), parser)
        except etree.XMLSyntaxError:
            self.fail(msg='The output was not valid html/xml!')


if __name__ == '__main__':
    unittest.main()
