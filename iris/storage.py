# -*- coding: utf-8 -*-
# This module contains all file handling/storage management/ID mapping methods

from lock import lock
from . import irisconfig
from .irisexceptions import IrisStorageViolationException, IrisNoSuchStorageBin

import os
import fnmatch
import re

# Sanitizes a given path with respect to a base os.path. Returns an absolute path
# garantueed to be beneath base_os.path.
def _sanitize_path(base_path, *paths):
    if len(paths) < 1:
        raise IrisStorageViolationException('Path not beneath STORAGE_PATH')
    base_path = os.path.expanduser(base_path)
    base_path = os.path.abspath(base_path)
    rel_path = os.path.abspath(os.path.join(base_path, *paths))
    if os.path.commonprefix([os.path.normpath(rel_path),
                          os.path.normpath(base_path)]) == base_path:
        return rel_path
    else:
        raise IrisStorageViolationException('Path not beneath STORAGE_PATH')

def get_abs_path(jobID, *path):
    """
    Returns the absolute path of a file.
    """
    if len(path) < 1:
        raise IrisStorageViolationException('Path not beneath STORAGE_PATH')
    # Run twice to ensure resulting path is beneath jobID.
    return _sanitize_path(_sanitize_path(irisconfig.STORAGE_PATH, jobID), *path)

def get_storage_path(path):
    """
    Converts an absolute path to a storage tuple of the form (id, path).
    """
    base_path = _sanitize_path(irisconfig.STORAGE_PATH, u'')
    if os.path.commonprefix([os.path.normpath(base_path),
            os.path.normpath(path)]) != base_path:
        raise IrisStorageViolationException('Path not beneath STORAGE_PATH')
    path = path.replace(base_path, u'', 1)
    m = re.match('^(?P<id>.+?)\/(?P<p>.+)', path)
    id = os.path.split(m.groupdict()['id'])[1]
    if is_valid_job(id):
        return (id, m.groups()[1])
    else:
        raise IrisNoSuchStorageBin('ID ' + m.groupdict()['id'] + ' not known.')

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
    """
    return os.path.isdir(_sanitize_path(irisconfig.STORAGE_PATH, jobID))


def prepare_filestore(jobID):
    """
    Prepares the default filestore to accept files for a job. Returns 'None' on
    failure, job ID on success.
    """
    if is_valid_job(jobID):
        return None
    try:
        jobPath = _sanitize_path(irisconfig.STORAGE_PATH, jobID)
        os.mkdir(jobPath)
        return jobID
    except Exception as err:
        return None


def list_content(jobID, pattern=u'*'):
    """
    Lists all files to a job ID, optionally applying a glob-like filter.
    """
    if not is_valid_job(jobID):
        return None
    flist = []
    jpath = _sanitize_path(irisconfig.STORAGE_PATH, jobID)
    for root, dirs, files in os.walk(jpath):
        flist.extend([os.path.relpath(os.path.join(root, s), jpath) for s in files])
    return fnmatch.filter(flist, pattern)


def retrieve_content(jobID, documents=None):
    """
    Retrieves data from a single or a list of documents. Returns binary data,
    for retrieving unicode text use retrieve_text().
    """
    if not is_valid_job(jobID):
        return None
    if documents:
        if isinstance(documents, basestring):
            documents = [documents]
        fdict = {}
        dpath = _sanitize_path(irisconfig.STORAGE_PATH, jobID)
        locks = [lock(_sanitize_path(dpath, doc)) for doc in documents]
        # will wait indefinitely until a lock can be acquired.
        map(lambda x: x.acquire(), locks)
        for doc in documents:
            with open(_sanitize_path(dpath, doc), 'rb') as f:
                fdict[doc] = f.read()
        return fdict
        map(lambda x: x.release(), locks)


def retrieve_text(jobID, documents=None):
    """
    Retrieves UTF-8 encoded text from a single or a list of documents.
    """
    res = retrieve_content(jobID, documents)
    return {t: res[t].decode('utf-8') for t in res}


def write_content(jobID, dest, data):
    """
    Writes data to a document at a destination beneath a jobID. Writes bytes,
    does not accept unicode objects; use write_text() for that.
    """
    if not is_valid_job(jobID):
        return None
    if not isinstance(data, basestring):
        return None
    try:
        with open(_sanitize_path(irisconfig.STORAGE_PATH,
                                 os.path.join(jobID, dest)), 'wb') as f:
            l = lock(f.name)
            l.acquire()
            f.write(data)
            l.release()
    except:
        return None
    return len(data)


def write_text(jobID, dest, text):
    """
    Writes text data encoded as UTF-8 to a file beneath a jobID.
    """
    return write_content(jobID, dest, text.encode('utf-8'))
