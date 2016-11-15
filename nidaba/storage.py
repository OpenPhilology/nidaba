# -*- coding: utf-8 -*-
"""
nidaba.storage
~~~~~~~~~~~~~~

This module contains all file handling/storage management/ID mapping methods.
"""

from __future__ import unicode_literals, print_function, absolute_import


from nidaba.lock import lock
from nidaba.config import nidaba_cfg
from nidaba.nidabaexceptions import (NidabaStorageViolationException,
                                     NidabaNoSuchStorageBin)

import io
import os
import fnmatch
import re

from flask_restful import url_for

class StorageFile(io.IOBase):
    """
    A file-like interface to a file on the storage medium.
    """

    def __init__(self, jobID, path, *args, **kwargs):
        self.path = get_abs_path(jobID, path)
        self.lock = lock(self.path)
        self.lock.acquire()
        try:
            self.fd = io.OpenWrapper(self.path, *args, **kwargs)
        except:
            self.lock.release()
            raise

    def __del__(self):
        try:
            self.fd.close()
            self.lock.release()
        except:
            pass

    def readable(self):
        return self.fd.readable()

    def writable(self):
        return self.fd.writable()

    def seekable(self):
        return self.fd.seekable()

    def read(self, size=-1):
        return self.fd.read(size)

    def readall(self):
        return self.fd.readall()

    def readinto(self, b):
        return self.fd.readinto()

    def write(self, msg):
        self.fd.write(msg)

    def writelines(self, lines):
        self.fd.writelines(lines)

    def seek(self, offset):
        self.fd.seek(offset)

    def tell(self):
        return self.fd.tell()

    def close(self):
        self.fd.close()
        self.lock.release()

    @property
    def closed(self):
        return self.fd.closed

    def isatty(self):
        return self.fd.isatty()

    def flush(self):
        self.fd.flush()

    def readline(self, limit=-1):
        return self.fd.readline(limit)

    def readlines(self, hint=-1):
        return self.fd.readlines(hint)

    @property
    def abs_path(self):
        return self.path

    @property
    def storage_path(self):
        return get_storage_path(self.path)


def _sanitize_path(base_path, *paths):
    """
    Sanitizes a given path with respect to a base path.

    Args:
        base_path (unicode): A base path beneath the concatenation of *paths is
        garantueed to be in.
        *paths (unicode): A list of subpaths which are concatenated and then
        checked if they are beneath base_path.

    Returns:
        (unicode): A string of the absolute path of the concatenations of
                   *paths.

    Raises:
        NidabaStorageViolationException: The absolute path of *paths is not
                                         beneath base_path. And whatever the
                                         python standard library decides to
                                         raise this week.
    """

    if len(paths) < 1:
        raise NidabaStorageViolationException('Path not beneath STORAGE_PATH')
    base_path = os.path.expanduser(base_path)
    base_path = os.path.abspath(base_path)
    rel_path = os.path.abspath(os.path.join(base_path, *paths))
    if os.path.commonprefix([os.path.normpath(rel_path),
                             os.path.normpath(base_path)]) == base_path:
        return rel_path
    else:
        raise NidabaStorageViolationException('Path not beneath STORAGE_PATH')


def is_file(jobID, path):
    """
    Checks if a storage tuple is a regular file.

    Args:
        jobID (unicode): An unique ID associated with a particular job.
        path (unicode): A path of a file beneath jobID.

    Returns:
        bool: Either True or False depending on the existence of the file.

    Raises:
        Exception: Who the fuck knows. The python standard library doesn't
                   document such paltry information as exceptions.
    """
    return os.path.isfile(get_abs_path(jobID, path))


def get_url(jobID, *paths):
    """
    Returns the URL on the api server for a file tuple.
    Args:
        jobID (unicode): A unique job ID
        *path (unicode): A list of path components that are concatenated to
        calculate the absolute path.

    Returns:
        (unicode): A string containing the absolute path of the storage tuple.
    """
    from nidaba import api
    app = api.create_app()
    app.config['SERVER_NAME'] =  nidaba_cfg['nidaba_server']
    with app.app_context():
        return url_for('api.page', batch=jobID, file=os.path.join(*paths))
    raise NidabaStorageViolationException('Invalid path')


def get_abs_path(jobID, *path):
    """
    Returns the absolute path of a file.

    Takes a job ID and a sequence of path components and checks if their
    absolute path is in the directory of that particular job ID.

    Args:
        jobID (unicode): A unique job ID
        *path (unicode): A list of path components that are concatenated to
        calculate the absolute path.

    Returns:
        (unicode): A string containing the absolute path of the storage tuple.

    Raises:
        NidabaStorageViolationException: The resulting absolute path is
                                         either not in the storage_path of the
                                         nidaba configuration or not in its job
                                         directory.
    """
    if len(path) < 1:
        raise NidabaStorageViolationException('Path not beneath STORAGE_PATH')
    # Run twice to ensure resulting path is beneath jobID.
    return _sanitize_path(_sanitize_path(nidaba_cfg['storage_path'], jobID),
                          *path)


def get_storage_path(path):
    """
    Converts an absolute path to a storage tuple of the form (id, path).

    Args:
        path (unicode): A unicode string of the absolute path.

    Returns:
        tuple: (id, path)

    Raises:
        NidabaStorageViolationException: The given path can not be converted
                                         into a storage tuple.
        NidabaNoSuchStorageBin: The given path is not beneath a valid job ID.
    """
    base_path = _sanitize_path(nidaba_cfg['storage_path'], u'')
    if os.path.commonprefix([os.path.normpath(base_path),
                             os.path.normpath(path)]) != base_path:
        raise NidabaStorageViolationException('Path not beneath STORAGE_PATH')
    path = path.replace(base_path, u'', 1)
    m = re.match('^(?P<id>.+?)\/(?P<p>.+)', path)
    id = os.path.split(m.groupdict()['id'])[1]
    if is_valid_job(id):
        return (id, m.groups()[1])
    else:
        raise NidabaNoSuchStorageBin('ID ' + m.groupdict()['id'] + ' not\
                                     known.')


def insert_suffix(orig_path, *suffix):
    """
    Inserts one or more suffixes just before the file extension.
    """
    pathname, extension = os.path.splitext(orig_path)
    for i in suffix:
        pathname += u'_' + i
    return pathname + extension


def is_valid_job(jobID):
    """
    Checks if filestore has been prepared for a job.

    Args:
        jobID (unicode): An identifier of a job.

    Returns:
        bool: True if job is already in the system, False otherwise.

    Raises:
        Standard python library caveats apply.
    """
    return os.path.isdir(_sanitize_path(nidaba_cfg['storage_path'], jobID))


def prepare_filestore(jobID):
    """
    Prepares the default filestore to accept files for a job.

    Args:
        jobID (unicode): Identifier of the bin to be created.

    Raises:
        NidabaStorageViolationException if the job ID already exists.
    """
    if is_valid_job(jobID):
        raise NidabaStorageViolationException(jobID + ' already exists')
    try:
        jobPath = _sanitize_path(nidaba_cfg['storage_path'], jobID)
        os.mkdir(jobPath)
    except Exception:
        raise NidabaStorageViolationException(jobID + ' already exists')


def list_content(jobID, pattern=u'*'):
    """
    Lists all files to a job ID, optionally applying a glob-like filter.

    Args:
        jobID (unicode): Identifier of the bin
        pattern (unicode): glob-like filter to match files

    Returns:
        list: A list of unicode strings of the matching files.

    Raises:
        NidabaNoSuchStorageBin if the job identifer is not known.
    """
    if not is_valid_job(jobID):
        raise NidabaNoSuchStorageBin('ID ' + jobID + ' not known.')
    flist = []
    jpath = _sanitize_path(nidaba_cfg['storage_path'], jobID)
    for root, dirs, files in os.walk(jpath):
        flist.extend([os.path.relpath(os.path.join(root, s), jpath)
                      for s in files])
    return fnmatch.filter(flist, pattern)


def retrieve_content(jobID, documents=None):
    """
    Retrieves data from a single or a list of documents. Returns binary data,
    for retrieving unicode text use retrieve_text().

    Args:
        jobID (unicode): Identifier of the bin
        documents (tuple or list of tuples): Documents to read in

    Returns:
        Dictionary: A dictionary mapping file identifiers to their contents.

    Raises:
        NidabaNoSuchStorageBin if the job identifer is not known.
    """
    if not is_valid_job(jobID):
        raise NidabaNoSuchStorageBin('ID ' + jobID + ' not known.')
    if documents:
        if isinstance(documents, basestring):
            documents = [documents]
        fdict = {}
        dpath = _sanitize_path(nidaba_cfg['storage_path'], jobID)
        locks = [lock(_sanitize_path(dpath, doc)) for doc in documents]
        map(lambda x: x.acquire(), locks)
        for doc in documents:
            with open(_sanitize_path(dpath, doc), 'rb') as f:
                fdict[doc] = f.read()
        map(lambda x: x.release(), locks)
        return fdict


def retrieve_text(jobID, documents=None):
    """
    Retrieves UTF-8 encoded text from a single or a list of documents.

    Args:
        jobID (unicode): Identifier of the bin
        documents (tuple or list of tuples): Documents to read in

    Returns:
        Dictionary: A dictionary mapping file identifiers to their contents.

    Raises:
        NidabaNoSuchStorageBin if the job identifer is not known.
    """
    res = retrieve_content(jobID, documents)
    return {t: res[t].decode('utf-8') for t in res}


def write_content(jobID, dest, data):
    """
    Writes data to a document at a destination beneath a jobID. Writes bytes,
    does not accept unicode objects; use write_text() for that.

    Args:
        jobID (unicode): Identifier of the bin.
        dest (tuple): Documents to write to.
        data (str): Data to write.

    Returns:
        int: Length of data written
    """
    if not is_valid_job(jobID):
        raise NidabaNoSuchStorageBin('ID ' + jobID + ' not known.')
    if not isinstance(data, basestring):
        raise NidabaStorageViolationException('data is not string')
    with open(_sanitize_path(nidaba_cfg['storage_path'],
                             os.path.join(jobID, dest)), 'wb') as f:
        l = lock(f.name)
        l.acquire()
        f.write(data)
        l.release()
    return len(data)


def write_text(jobID, dest, text):
    """
    Writes text data encoded as UTF-8 to a file beneath a jobID.

    Args:
        jobID (unicode): Identifier of the bin.
        dest (tuple): Documents to write to.
        text (unicode): Data to write.

    Returns:
        int: Length of data written
    """
    return write_content(jobID, dest, text.encode('utf-8'))
