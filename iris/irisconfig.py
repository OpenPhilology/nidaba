# -*- coding: utf-8 -*-
# The home directory for Iris to store files created by OCR jobs. For example,
# tifs, jp2s, meta.xml, and abbyy file downloaded from archive.org are stored
# here. Each new job is automatically placed in a uniquely named subdir named
# after its archiveID, creator, and timestamp.
IRIS_HOME = '~/OCR'	

# The prefix of the URL for archive.org downloads, which will have the
# remainder dynamically appended to it based on a job's archiveID.  For
# example, if we wish to process archive mechanicaesynta00philgoog, Iris will
# generate
# 'http://www.archive.org/download/mechanicaesynta00philgoog/mechanicaesynta00philgoog_tif.zip'
# automatically.
ARCHIVE_URL = 'http://www.archive.org/download'

# Storage backend URL. Can be any supported by pyfilesystem, e.g. FTP, RAM
# disks, S3, or native fs. If local file system is used (the default), the
# protocol field is not obligatory.
# URLS have to be of the following format:
# [type://][username[:password]@]hostname[:port][path]
STORAGE_PATH = '~/OCR'
# Example for ephemeral in memory storage
#STORAGE_URL = 'mem://'
# Example for FTP backend
#STORAGE_URL = 'ftp://username:password@somelocation.me/OCR'
