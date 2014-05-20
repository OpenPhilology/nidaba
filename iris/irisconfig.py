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

# Postprocessing configuration

# Spell check configuration

# We use the hunspell spell checker as it's the only one with decent unicode
# support, n-gram similarity, and flexibility to encode a wide array of
# language peculariarities through affix files. It is configured by defining
# tuples of the format (dictionary, affix-rules). Affix rules are optional if
# the dictionary does not contain them, but will reduce memory utilization
# greatly and they contain the dictionary encoding. Refer to the hunspell
# documentation for more information.
LANG_DICTS = { 'polytonic_greek': ('greek.dic',),  'lojban': ('test/lojban.txt',), 'german': ('test/german.txt',)}
# A default affix file is necessary to determine the encoding for dictionaries
# which don't have an own one. We default to UTF-8. 
DEFAULT_AFFIX = 'default.aff'

# Dictionary base path. This is the same format as STORAGE_URL, but only works
# with local file systems.
DICT_PATH = './dictionaries'
