# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile

from mock import patch, MagicMock

thisfile = os.path.abspath(os.path.dirname(__file__))


class KrakenTests(unittest.TestCase):

    """
    Tests for the kraken plugin.
    """

    def setUp(self):
        config_mock = MagicMock()
        storage_path = unicode(tempfile.mkdtemp())
        config_mock.nidaba_cfg = {
            'storage_path': storage_path,
        }

        self.patches = {
            'nidaba.config': config_mock,
        }
        self.patcher = patch.dict('sys.modules', self.patches)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()
        self.storage_path = storage_path
        from nidaba import storage
        self.storage = storage

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.storage_path)

if __name__ == '__main__':
    unittest.main()
