# -*- coding: utf-8 -*-
# The home directory for Iris to store files created by OCR jobs. For example,
# tifs, jp2s, meta.xml, and abbyy file downloaded from archive.org are stored
# here. Each new job is automatically placed in a uniquely named subdir named
# after its archiveID, creator, and timestamp.
STORAGE_PATH = u'~/OCR'

# Spell check configuration. Dictionaries are kept on the common medium (i.e.
# at STORAGE_PATH/tuple[0]/tuple[1]).
LANG_DICTS = { u'polytonic_greek': (u'dicts', u'greek.dic'), 
               u'lojban': (u'dicts', u'test/lojban.txt'), 
               u'german': (u'dicts', u'test/german.txt')}

# Old tesseract version create hOCR files ending in .html, current ones .hocr
OLD_TESSERACT = False

# Ocropus configuration
OCROPUS_MODELS = { u'greek': (u'models', u'greek.pyrnn.gz'),
                   u'atlantean': (u'models', u'atlantean.pyrnn.gz'),
                   u'fraktur': (u'models', u'fraktur.pyrnn.gz')}
