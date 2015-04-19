# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile

from lxml import etree
from distutils import spawn
from nidaba.plugins import kraken 

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, 'resources'))


class OcropusTests(unittest.TestCase):

    """
    Tests for python ocropus bindings.
    """

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_file_outpath_png(self):
        """
        Test that kraken creates hocr output for pngs.
        """
        pass
