# -*- coding: utf-8 -*-
import unittest
import hocr
import re
import tempfile

class HocrTests(unittest.TestCase):
    """
    Tests algorithms dealing with hocr manipulation.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryFile()

    def tearDown(self):
        self.temp.close()
        

    def test_simple_word_extract(self):
        self.temp.write("""<html><body><span class='ocrx_word' id='word_10' title="bbox 260 196 305 232">εἰς</span></body><html>""")
        self.temp.seek(0,0)
        for t in hocr.extract_hocr_tokens(self.temp):
            self.assertEqual('εἰς'.decode('utf-8'), t)

    def test_bbox_extract_simple(self):
        """"
        Test hocr bbox extraction in some simple cases.
        """
        self.temp.write(u'<root title="bbox 1 2 3 4"></root>')
        self.temp.seek(0,0)
        bboxes = hocr.extract_bboxes(self.temp)
        self.assertEqual([(1, 2, 3, 4)], bboxes)

    def test_bbox_extract_complex(self):
        """
        Test hocr bbox extraction on a larger document which exercises 
        the bbox identifying regex.
        """
        self.temp.write(u"""<root>"""
                         """<p title="text before bbox 1 2 3 4"></p>"""
                         """<p title="bbox 5 6 7 8textafter"></p>"""
                         """<p title="textbeforebbox 9 10 11 12textafter"></p>"""
                         """</root>""")
        self.temp.seek(0,0)

        bboxes = hocr.extract_bboxes(self.temp)
        self.assertEqual((1, 2, 3, 4), bboxes[0])
        self.assertEqual((5, 6, 7, 8), bboxes[1])
        self.assertEqual((9, 10, 11, 12), bboxes[2])


if __name__ == '__main__':
	unittest.main()