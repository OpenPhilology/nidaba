import unittest
import os
import tempfile
import glob
import difflib

from iris import abbyyToOCR

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, u'resources/abbyyConversion'))

#The unit tests for abbyy to hOCR conversion. Each XML to HTML tag transform method is individually tested, then the output of a full conversion is compared against a directory of originals.
class TestAbbyyToOCRConversion(unittest.TestCase):
    def testConverstion(self):

        abbySample = open(os.path.join(resources, u'testAbbyy.xml'))
        tempdir = tempfile.mkdtemp()
        abbyyToOCR.convert_abbyy_to_ocr(abbySample, tempdir, u'testAbbyy')

        orig_count = len(glob.glob(os.path.join(resources, u'hocr/testHOCR_[0-9][0-9]*.hocr.html'))) # And not os.listdir(), which will include crap like .DS_Store.
        new_count = len(glob.glob(os.path.join(tempdir, u'testAbbyy_[0-9][0-9]*.hocr.html')))

        self.assertEqual(orig_count, new_count)

        for x in range(0, orig_count):
            orig_file = os.path.join(resources, u'hocr/testHOCR_%i.hocr.html' % x)
            new_file = os.path.join(tempdir, 'testAbbyy_%i.hocr.html' % x)
            with open(orig_file) as o:
                with open(new_file) as n:
                    diff = difflib.unified_diff(o.readlines(), n.readlines(), fromfile=orig_file, tofile=new_file)
                    for line in diff:
                        self.fail(msg='hocr output did not match the master copy. \n Differences: %s' % line)

if __name__ == '__main__':
    unittest.main()
