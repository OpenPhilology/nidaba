#! /usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import storage
import irisconfig
import uuid
from os import path

from tempfile import mkdtemp

class test_storage(unittest.TestCase):
    '''
    Tests the storage backend.
    '''

    def test_prepare_filestore(self):
        '''Tests if filestore is preparing directories for new jobs correctly.'''
        
        id = unicode(uuid.uuid4())
        self.assertEqual(id, storage.prepare_filestore(id), 'Preparing filestore failed.')
        self.assertTrue(storage.is_valid_job(id), 'Directory structure incorrect.')

    def test_write_content(self):
        '''Tests (binary) content writing.'''
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(id)
        f = u'bananagram'
        d = 3 * '\x01\x02\x03\x04\x05\x99'
        self.assertEqual(len(d), storage.write_content(id, f, d), 'Writing data failed.')
        with open(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)), 'rb') as f:
            self.assertEqual(d, f.read(), 'Retrieved data does not match written data.')

    def test_write_text(self):
        '''Tests (text) content writing.'''
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(id)
        f = u'bananagram'
        d = 3 * u'bananaøö«¬áßðgï '
        storage.write_text(id, f, d)
        with open(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)), 'rb') as f:
            self.assertEqual(d, f.read().decode('utf-8'), 'Retrieved data does not match written data.')

    def test_retrieve_content(self):
        '''Tests (binary) content retrieval.'''
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(id)
        f = u'bananagram'
        d = 3 * u'banana '
        with open(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)), 'wb') as fi:
            fi.write(d.encode('utf-8'))
        r = storage.retrieve_content(id, f)
        self.assertDictEqual({f:d.encode('utf-8')}, storage.retrieve_content(id, f), 'Retrieved data not equal.')

    def test_retrieve_multiple_content(self):
        '''Tests retrieval of multiple documents at once.'''
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(id)
        fdict = {}
        for i in range(0, 2048):
            f = unicode(uuid.uuid4())
            fdict[f] = str(uuid.uuid4()) + '\x01\x02\x03\x99'
            with open(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)), 'wb') as fi:
                fi.write(fdict[f])
        self.assertDictEqual(fdict, storage.retrieve_content(id, fdict.keys()), 'Retrieved data does not match written data.')

    def test_retrieve_text(self):
        '''Tests (text) content retrieval.'''
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(id)
        f = u'bananagram'
        d = 3 * u'bananaøö«¬áßðgï '
        with open(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)), 'wb') as fi:
            fi.write(d.encode('utf-8'))
        self.assertEqual(d, storage.retrieve_text(id, f)[f], 'Retrieved data does not match written data.')

    def test_retrieve_multiple_text(self):
        '''Tests retrieval of multiple text documents.'''
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(id)
        fdict = {}
        for i in range(0, 2048):
            f = unicode(uuid.uuid4())
            fdict[unicode(f)] = unicode(uuid.uuid4())
            with open(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)), 'wb') as fi:
                fi.write(fdict[f].encode('utf-8'))
        self.assertDictEqual(fdict, storage.retrieve_content(id, fdict.keys()), 'Retrieved data does not match written data.')

    def test_list_content(self):
        '''Tests listing of content to a job.'''
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(id)
        fdict = {}
        for i in range(0, 2048):
            f = unicode(uuid.uuid4())
            fdict[unicode(f)] = unicode(uuid.uuid4())
            with open(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)), 'wb') as fi:
                fi.write(fdict[f].encode('utf-8'))
        self.assertSetEqual(set(fdict.keys()), set(storage.list_content(id)), 'Written document names do not match read document names.')

if __name__ == '__main__':
    unittest.main()
