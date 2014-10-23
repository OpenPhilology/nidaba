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

STORAGE_PATH = '~/OCR'

# Postprocessing configuration

# Spell check configuration

LANG_DICTS = { 'polytonic_greek': 'greek.dic',  'lojban': 'test/lojban.txt', 'german': 'test/german.txt'}
DICT_PATH = './dictionaries'

# Old tesseract version create hOCR files ending in .html, current ones .hocr
OLD_TESSERACT = False
