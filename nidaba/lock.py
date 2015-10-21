# -*- coding: utf-8 -*-
"""
nidaba.lock
~~~~~~~~~~~

This module contains an NFS-safe locking method that is hopefully interoperable
with anything anybody is going to encounter out there.
"""

from __future__ import unicode_literals, print_function, absolute_import

import os
import time
import random

from nidaba.nidabaexceptions import NidabaStorageViolationException

class lock(object):
    """
    A global lock implementation for files on the common storage medium. It is
    intended to be mainly used on NFS although it should work on any network
    file system.
    """
    def __init__(self, locked_file):
        """
        Initialize a lock object.

        Args:
            locked_file (unicode): Path to the file to be locked
        """
        self._locked_file = locked_file + u'.lock'
        self._lock_file = unicode(os.uname()[1]) + u'.' + \
            unicode(os.getpid()) + u'.lock'

    def acquire(self):
        """
        Acquires a lock on the selected file. Waits until the lock can be
        acquired except when the directory components of the path does not
        exist.
        """
        if not os.path.isdir(os.path.dirname(self._locked_file)):
            raise NidabaStorageViolationException('Path to locked file does not exist.')
        while True:
            try:
                os.symlink(self._lock_file, self._locked_file)
                break
            except Exception as e:
                if os.path.islink(self._locked_file) and \
                   os.readlink(self._locked_file) == self._lock_file:
                    break
            time.sleep(random.random() + 0.001)

    def release(self):
        """
        Releases the lock on the selected file.

        Returns:
            bool: True if the lock has been releases, False otherwise
        """
        if os.path.islink(self._locked_file) and \
           os.readlink(self._locked_file) == self._lock_file:
            try:
                os.remove(self._locked_file)
                return True
            except:
                pass
        return False
