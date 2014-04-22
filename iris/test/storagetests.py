# -*- coding: utf-8 -*-
import unittest
import storage
import uuid
from fs import utils,path

from tempfile import mkdtemp

class StorageTests(unittest.TestCase):
    '''
    Tests the storage backend.
    '''

    def test_filestore_mounting_tmp(self):
        '''Tests mounting of a temporary file system directory.'''
        d = mkdtemp()
        self.assertIsNotNone(storage.mount_filestore(d))
    
    def test_filestore_mounting_mem(self):
        '''Tests mounting of a memory backed storage backend.'''
        self.assertIsNotNone(storage.mount_filestore('mem://'))

    def test_prepare_filestore(self):
        '''Tests if filestore is preparing directories for new jobs correctly.'''
        stor = storage.mount_filestore('mem://')
        id = unicode(uuid.uuid4())
        self.assertEqual(id, storage.prepare_filestore(stor, id), 'Preparing filestore failed.')
        self.assertTrue(stor.isdir(id), 'Directory structure incorrect.')

    def test_write_content(self):
        '''Tests content writing.'''
        stor = storage.mount_filestore('mem://')
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(stor, id)
        f = u'bananagram'
        d = 3 * u'banana '
        self.assertEqual(len(d), storage.write_content(stor, id, f, d), 'Writing data failed.')
        self.assertEqual(d, stor.getcontents(path.join(id, f)), 'Retrieved data is not equal to written data.')

    def test_retrieve_content(self):
        '''Tests content retrieval.'''
        stor = storage.mount_filestore('mem://')
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(stor, id)
        f = u'bananagram'
        d = 3 * u'banana '
        stor.setcontents(path.join(id, f), d)
        self.assertDictEqual({f:d}, storage.retrieve_content(stor, id, f), 'Retrieved data not equal.')

    def test_retrieve_multiple_content(self):
        '''Tests retrieval of multiple documents at once.'''
        stor = storage.mount_filestore('mem://')
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(stor, id)
        fdict = {}
        for i in range(0, 2048):
            f = unicode(uuid.uuid4())
            fdict[unicode(f)] = unicode(uuid.uuid4())
            stor.setcontents(path.join(id, f), fdict[f])
        self.assertDictEqual(fdict, storage.retrieve_content(stor, id, fdict.keys()), 'Retrieved data does not match written data.')

    def test_list_content(self):
        '''Tests listing of content to a job.'''
        stor = storage.mount_filestore('mem://')
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(stor, id)
        fdict = {}
        for i in range(0, 2048):
            f = unicode(uuid.uuid4())
            fdict[unicode(f)] = unicode(uuid.uuid4())
            stor.setcontents(path.join(id, f), fdict[f])
        self.assertListEqual(fdict.keys(), storage.list_content(stor, id), 'Written document names do not match read document names.')

if __name__ == '__main__':
    unittest.main()
