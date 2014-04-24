# -*- coding: utf-8 -*-
# This module contains all file handling/storage management/ID mapping methods

import fs
from fs import path, errors
from fs.opener import opener
from cStringIO import StringIO

# Mounts a/the storage backend from fs_url. Format is described in the
# configuration file.
def mount_filestore(fs_url, attempts=10):
    rfs = None
    tries = 0
    while(tries < attempts):
        try:
            rfs = opener.opendir(fs_url)
            if not rfs.getmeta('thread_safe'):
                pass
                # FIXME: find out how to to proper celery based logging 
                # log.warn('Filestore is not thread safe! Make sure to run only'
                #        'a single celery worker on the queue at all times or'
                #        'use a thread safe backend.')
            break
        except:
            tries += 1
    return rfs

# Unmounts a file store
def umount_filestore(stor):
    stor.close()

# Prepares the filestore to accept data for a job ID. Returns 'None' on
# failure, job ID on success.
def prepare_filestore(stor, jobID):
    try:
        stor.makedir(jobID)
        return jobID
    except Exception as err:
        # log.debug('Filestore preparation failed for job: ' + jobID)
        # log.debug(err)
        return None

# Retrieves a list of all files to a job ID
def list_content(stor, jobID):
    walk = stor.walkfiles(jobID)
    return [f[f.find(jobID) + len(jobID) + 1:] for f in walk]

# Returns a dict containing the content of specified doc(s)
def retrieve_content(stor, jobID, documents=None):
    if documents:
        if isinstance(documents, basestring):
            documents = [documents]
        return {d:stor.getcontents(fs.path.join(jobID, d)) for d in documents}
    else:
        return {}

# Writes a document to a path below a job.
def write_content(stor, jobID, dest, data):
    try:
        stor.setcontents(fs.path.join(jobID, dest), data)
        return len(data)
    except:
        # log.debug('Writing content for job: ' + jobID + ' failed.')
        # log.debug(err)
        return None
