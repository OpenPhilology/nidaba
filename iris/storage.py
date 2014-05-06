# -*- coding: utf-8 -*-
# This module contains all file handling/storage management/ID mapping methods

# Not a good way to lock files. Unfortunately flock is an abomination unto the
# FSM, doesn't work with all NFS implementations and releases all locks on file
# closure and then reacquires them (non-atomically).
from lockfile import FileLock
from os import path
import irisconfig
import os
import fnmatch


# Sanitizes a given path with respect to a base path. Returns an absolute path
# garantueed to be beneath base_path.
def _sanitize_path(base_path, rel_path):
    base_path = path.expanduser(base_path)
    base_path = path.abspath(base_path)
    rel_path = path.abspath(path.join(base_path, rel_path))
    if path.commonprefix([path.normpath(rel_path), path.normpath(base_path)]) == base_path:
        return rel_path
    else:
        return ''

# Checks if filestore has been prepared for a job.
def _is_valid_job(jobID):
    return path.isdir(_sanitize_path(irisconfig.STORAGE_URL, jobID))

def prepare_filestore(jobID):
    """
    Prepares the default filestore to accept files for a job. Returns 'None' on
    failure, job ID on success.
    """
    if _is_valid_job(jobID):
        return None
    try:
        jobPath = _sanitize_path(irisconfig.STORAGE_URL, jobID)
        os.mkdir(jobPath)
        return jobID
    except Exception as err:
        return None

def list_content(jobID, pattern='*'):
    """
    Lists all files to a job ID, optionally applying a glob-like filter.
    """
    if not _is_valid_job(jobID):
        return None
    flist = []
    jpath = _sanitize_path(irisconfig.STORAGE_URL, jobID)
    for root, dirs, files in os.walk(jpath):
        flist.extend([path.relpath(path.join(root, s), jpath) for s in files])
    return fnmatch.filter(flist, pattern)

def retrieve_content(jobID, documents=None):
    """
    Retrieves data from a single or a list of documents. Returns binary data,
    for retrieving unicode text use retrieve_text().
    """
    if not _is_valid_job(jobID):
        return None
    if documents:
        if isinstance(documents, basestring):
            documents = [documents]
        fdict = {}
        dpath = _sanitize_path(irisconfig.STORAGE_URL, jobID)
        locks = [FileLock(_sanitize_path(dpath, doc)) for doc in documents]
        # will wait indefinitely until a lock can be acquired.
        map(lambda x: x.acquire(), locks)
        for doc in documents:
            with open(_sanitize_path(dpath, doc), 'rb') as f:
                fdict[doc] = f.read()
        map(lambda x: x.release(), locks)
        return fdict

def retrieve_text(jobID, documents=None):
    """
    Retrieves UTF-8 encoded text from a single or a list of documents.
    """
    res = retrieve_content(jobID, documents)
    return {t:res[t].decode('utf-8') for t in res}

def write_content(jobID, dest, data):
    """
    Writes data to a document at a destination beneath a jobID. Writes bytes,
    does not accept unicode objects; use write_text() for that.
    """
    if not _is_valid_job(jobID):
        return None
    if not isinstance(data, basestring):
        return None
    try:
        with open(_sanitize_path(irisconfig.STORAGE_URL, path.join(jobID, dest)), 'wb') as f:
            lock = FileLock(f.name)
            lock.acquire()
            f.write(data)
            lock.release()
    except:
        return None
    return len(data)

def write_text(jobID, dest, text):
    """
    Writes text data encoded as UTF-8 to a file beneath a jobID.
    """
    return write_content(jobID, dest, text.encode('utf-8'))

## Writes a document to a path below a job.
#def write_content(stor, jobID, dest, data):
#    try:
#        stor.setcontents(fs.path.join(jobID, dest), data)
#        return len(data)
#    except:
#        # log.debug('Writing content for job: ' + jobID + ' failed.')
#        # log.debug(err)
#        return None
