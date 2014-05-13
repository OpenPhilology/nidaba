#! /usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import storage
import time
import uuid
import irisconfig
from os import path
from multiprocessing import Process
from lock import lock

class LockTests(unittest.TestCase):
    """
    Tests the locking implementation.
    """
    def test_lock_acquisition(self):
        """
        Tests if simple lock acquiral and release works.
        """
        id = unicode(uuid.uuid4())
        storage.prepare_filestore(id)
        f = u'bananagram'
        l = lock(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)))
        l.acquire()
        self.assertTrue(l.release(), u"Lock acquisition failed.")

    def test_lock_functionality(self):
        """
        Test if locks actually lock anything.
        """
        def acquire(id, f):
            l = lock(storage._sanitize_path(irisconfig.STORAGE_PATH, path.join(id, f)))
            l.acquire()
            time.sleep(0.25)
            l.release()

        id = unicode(uuid.uuid4())
        f = u'banananagram'
        storage.prepare_filestore(id)
        p = []
        for i in range(10):
            p.append(Process(target=acquire, args = (id, f)))
            p[-1].start()
        # the last process should have exited after 2.5 seconds
        time.sleep(5)
        self.assertEqual(set([pr.is_alive() for pr in p]), {False}, u"Lock acquisition failed. Manual cleanup of locking processes required.")

if __name__ == '__main__':
    unittest.main()
