# -*- coding: utf-8 -*-
# This module contains an NFS-safe locking method that is hopefully
# interoperable with anything anybody is going to encounter out there.

import os
import time
import random


class lock:
    def __init__(self, locked_file):
        self._locked_file = locked_file + u'.lock'
        self._lock_file = unicode(os.uname()[1]) + u'.' + \
                          unicode(os.getpid()) + u'.lock'

    def acquire(self):
        while True:
            try:
                os.symlink(self._lock_file, self._locked_file)
                break
            except:
                if os.path.islink(self._locked_file) and \
                   os.readlink(self._locked_file) == self._lock_file:
                    break
            time.sleep(random.random() + 0.001)

    def release(self):
        if os.path.islink(self._locked_file) and \
           os.readlink(self._locked_file) == self._lock_file:
            try:
                os.remove(self._locked_file)
                return True
            except:
                pass
        return False
