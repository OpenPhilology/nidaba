# -*- coding: utf-8 -*-
#This module contains all celery tasks. All tasks should be try-except safed, to guarantee A:graceful recovery from a failed OCR task, and B:immediate point-of-failure indentification for debugging purposes, or to easily identify bad OCR data.
import celeryConfig
import irisconfig
import uuid
import logging
import inspect
import time
import gzip
import zipfile
import requests
import fs
import algorithms

from celery import Celery
from celery import group
from celery import chord
from celery.task.sets import TaskSet
from celery.utils.log import get_task_logger
from requests import HTTPError, ConnectionError, Timeout
from fs import path, errors
from fs.opener import opener
from cStringIO import StringIO
from storage import *

app = Celery(main='tasks', broker=celeryConfig.BROKER_URL)
app.config_from_object('celeryConfig')

archive_url_format = 'http://www.archive.org/download/{0}/{0}{1}'

# ------------------------------------------------------------------------------------------
# The tasks. -------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------

@app.task(name='edit_distance_task')
def edit_distance_task(str1, str2):
    algorithms.edit_distance(str1, str2)
    

@app.task(name='http_download')
def http_download(username, password, url, path, fs_url=irisconfig.STORAGE_URL):
    """Download the contents of a url and store the result at the specified path."""

    filestore = mount_filestore(fs_url)
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with filestore.open(path, 'w+') as f:
            for chunk in r.iter_content():
                f.write(chunk)

    filestore.close()
    return path

@app.task(name='unzip_archive')
def unzip_archive(username, password, src, dst=None, fsaddr=irisconfig.STORAGE_URL):
    """Extract the contents of a zip archive and store them at the desired directory."""

    filestore = mount_filestore(fs_url)
    extractdir = dst if dst is not None else fs.path.dirname(src)

    with filestore.open(src) as fh:    # Get a standard python file-like object from the filestore.
        with zipfile.ZipFile(fh) as zfh:    # Get a zip object from the file object.
            for name in zfh.namelist():                # For every item in that zip archive...
                with zfh.open(name) as extracted_file:     # Get a standart python file-like object from which we can read decompressed data.
                    realname = fs.path.basename(name)
                    filepath = fs.path.join(extractdir, realname)
                    filestore.createfile(filepath)
                    filestore.setcontents(filepath, extracted_file.read())

    filestore.close()
    return extractdir

# @app.task(name='get_archive.org_archive')
# def get_org_archive(archive_name, username, password, fsaddr=irisconfig.FTP_ADDR):
#     """Retrieve an archive.org archive."""
#     filestore = mount_filestore(fsaddr,  username, password)
#     url = archive_url_format.format(archive_name, '_tif.zip')
    

# ------------------------------------------------------------------------------------------
# Test tasks -------------------------------------------------------------------------------
# These tasks were created for unit testing and should not be used for other purpose. ------
# ------------------------------------------------------------------------------------------

@app.task(name='test_ftp_connect')
def ftp_connect_task(addr, username, password):
    """Connect to the FTP file store, then immediately disconnect."""

    filestore = mount_test_filestore(username, password)
    filestore.close()
    return 'successful'

@app.task(name='create_test_file')
def create_test_file(addr, username, password, contents):
    """Create a file with a random name."""

    filestore = mount_test_filestore(username, password)
    path = str(uuid.uuid4())
    filestore.createfile(path)
    filestore.setcontents(path, contents)
    filestore.close()
    return path

@app.task(name='delete_file')
def delete_file(addr, username, password, path):
    """Delete a file for the shared file store"""

    filestore = mount_test_filestore(username, password)

    filestore.remove(path)
    filestore.close()
    return path

@app.task(name='create_dir')
def create_dir(addr, username, password):
    """Create a directory with a random name."""

    name = '/%s' % uuid.uuid4()
    filestore = mount_test_filestore(username, password)
    filestore.makedir(name)
    filestore.close()
    return name

@app.task(name='delete_dir')
def delete_dir(addr, username, password, path):
    """Delete a directory from the shared file store."""

    filestore = mount_test_filestore(username, password)
    filestore.removedir(path)
    filestore.close()
    return path


#Attempt to parse a file into an image and load it into memory. If this method returns an image, the image is guaranteed to be valid.
@app.task(name='imageLoadTask')
def imageFromFile(file):
    try:
        image = Image.open(file)   #Lazy; won't load until we access or force.
        image.load()               #..and force the load.
        log.debug('Image \"' + file.filename +'\" was valid!')
        return image
    except Exception as err:
        log.debug('Image was not valid')
        log.debug(err)
        return None

#Download an HTTP URL and return the content of the response.
@app.task(name='downloadURL')
def getURL(url):
    try:
        print('initiating request for '+str(url))
        r = requests.get(url)
        print('request for '+ str(url) + ' within task block')
        return r.content
    except ConnectionError:
        print('Network error retrieving {0}. Check network access'.format(url))
    except HTTPError:
        print('The response to {0} was invalid'.format(url))
    except Timeout:
        print('The request {0} timed out.'.format(url))
    except Exception as e:
        print('printing anomalous exception...')
        print(e)
        print('exception printed')
        # print('An anomalous exception occured when requesting {0}'.format(url))


#Opens a zip archive and returns its decompressed contents as a list of files (cStringIO types)
@app.task(name='unzipArchive')
def extractZipContents(file, **kwargs):
    try:
        zipArchive = zipfile.ZipFile(StringIO(file))
        extractedFiles = []
        for info in zipArchive.infolist():
            # print info.filename, info.date_time, info.file_size
            extractedFiles.append(zipArchive.open(info))
        return extractedFiles
    except Exception as e:
        print('Error, file was not a valid zip archive.')
        print(e)

@app.task
def extractGZipContents(file, **kwargs):
    print 'attempting gzip extraction'
    print 'file for gunzipping was type: ' + str(type(file))
    try:
        # archive = gzip.open(StringIO(file))
        # content = archive.read()
        # archive.close()
        archive = gzip.GzipFile(fileobj=StringIO(file))
        content = archive.read()
        archive.close()
        print(content[:100])
        return content
    except Exception as e:
        print 'failed to extract the zip archive'
        print e


@app.task
def processDownloadedArchive(*args, **kwargs):
    print 'Processsing downloaded archives.'
    for f in args[0]:
        print(f[:100])


@app.task(name='processArchive.orgVolumeAsGroup')
def processArchiveGroup(archiveId):
    taskSet = TaskSet([
            # getURL.subtask(args=['{0}/{1}/{1}_tif.zip'.format(archiveURL, archiveId)], link=testTask.s()),
            getURL.subtask(args=['{0}/{1}/{1}_meta.xml'.format(archiveURL, archiveId)], link=testTask.s())
            # getURL.subtask(args=['{0}/{1}/{1}_abbyy.gz'.format(archiveURL, archiveId)], link=testTask.s())
            ])
    result = taskSet.apply_async()
    print result.ready()

    while result.ready() != True:
        print 'spinlock'

    print 'results done!'
    print (result.join())



#The top level task for OCRign an archive from archive.org.If you want to OCR archive.org data, you call this task. All necessary subtasks are called automatically.
@app.task(name='processArchive.orgVolume')
def processOrgArchive(archiveId):
    header = [
            getURL.subtask(args=['{0}/{1}/{1}_tif.zip'.format(archiveURL, archiveId)], link=extractZipContents.s(myArg='tif')),
            getURL.subtask(args=['{0}/{1}/{1}_meta.xml'.format(archiveURL, archiveId)]),    
            getURL.subtask(args=['{0}/{1}/{1}_abbyy.gz'.format(archiveURL, archiveId)], link=extractGZipContents.s(myArg='gz'))
            ]
    chordCB = processDownloadedArchive.s(myArg='processing archive')
    downloadResults = chord(header)(chordCB)
    print downloadResults
    print type(downloadResults)
    print downloadResults.__class__

    while downloadResults.ready() != True:
        pass

    print 'all downloads complete'
    print downloadResults.get() #returns None
    print downloadResults.collect() #works
    
    print downloadResults.children  #returns None

    # theList = list(downloadResults.collect())
    # print 'thelist:' +str(theList)
    # print '" type ' +str(type(theList))
    # print '" class' +str(theList.__class__)
    # print 'thelist[0] ' + str(theList[0])
    # print '" type ' +str(type(theList[0]))
    # print '" class ' +str(theList[0].__class__)
    # print 'thelist[0][0] '+ str(theList[0][0].result)
    # print '" type ' +str(type(theList[0][0].result))
    # print '" class ' +str(theList[0][0].__class__)
    
    # theList2 = list(downloadResults.get())#returns None
    # print theList2
