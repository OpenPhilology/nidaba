import unittest
import os
import tempfile
import glob
import difflib
import abbyyToOCR

#The unit tests for abbyy to hOCR conversion. Each XML to HTML tag transform method is individually tested, then the output of a full conversion is compared against a directory of originals.
class TestAbbyyToOCRConversion(unittest.TestCase):
    def testConverstion(self):

        abbySample = open('./resources/abbyyConversion/testAbbyy.xml')
        tempdir = tempfile.mkdtemp()
        abbyyToOCR.convertAbbyyToOCR(abbySample, tempdir, 'testAbbyy')

        orig_count = len(glob.glob('resources/abbyyConversion/hocr/testHOCR_[0-9][0-9]*.hocr.html')) # And not os.listdir(), which will include crap like .DS_Store.
        new_count = len(glob.glob(os.path.join(tempdir, 'testAbbyy_[0-9][0-9]*.hocr.html')))

        self.assertEqual(orig_count, new_count)

        for x in range(0, orig_count):
            orig_file = 'resources/abbyyConversion/hocr/testHOCR_%i.hocr.html' % x
            new_file = os.path.join(tempdir, 'testAbbyy_%i.hocr.html' % x)
            with open(orig_file) as o:
                with open(new_file) as n:
                    diff = difflib.unified_diff(o.readlines(), n.readlines(), fromfile=orig_file, tofile=new_file)
                    for line in diff:
                        self.fail(msg='hocr output did not match the master copy. \n Differences: %s' % line)

if __name__ == '__main__':
    unittest.main()