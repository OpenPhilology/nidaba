# -*- coding: utf-8 -*-
#The home directory for Iris to store files created by OCR jobs. For example, tifs, jp2s, meta.xml, and abbyy file downloaded from archive.org are stored here. Each new job is automatically placed in a uniquely named subdir named after its archiveID, creator, and timestamp.
IRIS_HOME = '~/OCR'	

# The prefix of the URL for archive.org downloads, which will have the remainder dynamically appended to it based on a job's archiveID. 
# For example, if we wish to process archive mechanicaesynta00philgoog, 
# Iris will generate 'http://www.archive.org/download/mechanicaesynta00philgoog/mechanicaesynta00philgoog_tif.zip' automatically.
ARCHIVE_URL = 'http://www.archive.org/download'

# Addresss of the FTP server for large result and file storage. In a real deployment, some other system such as NFS can be used.
FTP_ADDR = ('localhost', 8001)

# Address of used to create temporary FTP servers used for unit testing.
FTP_TEST_ADDR = ('localhost', 8002)

# Address of used to create temporary HTTP servers used for unit testing.
HTTP_TEST_ADDR = ('localhost', 8003)