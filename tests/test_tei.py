# -*- coding: utf-8 -*-
import unittest
import StringIO
import itertools
import uuid
import os

from lxml import etree
from nidaba import tei
from nidaba.nidabaexceptions import NidabaRecordException

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, 'resources/schema'))

class TEITests(unittest.TestCase):

    """
    General tests for the OCRRecord module.
    """
    def setUp(self):
        self.record = tei.OCRRecord()
        for x in self.record.fields:
            setattr(self.record, x, str(uuid.uuid4()))
        id_1 = self.record.add_respstmt('bar', 'foo')
        id = self.record.add_respstmt('foo', 'bar')
        self.record.dimensions = (100, 100)
        for x in range(0, 10):
            self.record.add_line((0, 0, 0, 0))
        for x in range(0, 10):
            self.record.add_segment((0, 0, 0, 0), language='foo', confidence=80)
        self.record.add_graphemes([{'bbox': (0, 0, 0, 0), 
                               'confidence': 95,
                               'grapheme': ''.join(x)} for x in itertools.permutations('ABCD', 2)])
        self.record.add_choices('line_3', [{'confidence': 95,
                                       'alternative': ''.join(x)} for x in itertools.permutations('ABCD', 2)])
        self.record.add_choices('seg_1', [{'confidence': 95,
                                       'alternative': ''.join(x)} for x in itertools.permutations('ABCD', 2)])
        self.record.add_choices('grapheme_1', [{'confidence': 95,
                                           'alternative': ''.join(x)} for x in itertools.permutations('ABCD', 2)])
        # elements without responsibility statements
        self.record.reset_respstmt_scope()
        self.record.add_line((0, 0, 0, 0))
        self.record.add_segment((0, 0, 0, 0), language='foo', confidence=80)
        self.record.add_graphemes([{'bbox': (0, 0, 0, 0), 
                               'confidence': 95,
                               'grapheme': 'AB'}])
        self.record.add_choices('line_11', [{'confidence': 95,
                                           'alternative': ''.join(x)} for x in itertools.permutations('ABCD', 2)])

    def test_basic(self):
        """
        Tests basic functionality (adding lines, segments, graphemes,
        alternatives)
        """
        self.record = tei.OCRRecord()

        # test adding lines
        for x in range(0, 10):
            self.record.add_line((0, 0, 0, 0))
        self.assertEqual(len(self.record.lines), 10)

        # test scoping invalid line
        with self.assertRaises(NidabaRecordException):
            self.record.scope_line('foo')

        # test scoping valid line
        self.record.scope_line('line_1')
        self.assertEqual(self.record.line_scope, 'line_1')

        # test adding graphemes directly beneath lines
        self.record.scope_line('line_1')
        self.record.add_graphemes([{'bbox': (0, 0, 0, 0), 
                               'confidence': 95,
                               'grapheme': x} for x in itertools.permutations('ABCD', 2)])
        self.assertEqual(len(self.record.lines['line_1']['content']),
                         len(list(itertools.permutations('ABCD', 2))))

        # test adding segments
        self.record.scope_line('line_2')
        for x in range(0, 10):
            self.record.add_segment((0, 0, 0, 0), language='foo', confidence=80)
        self.assertEqual(len(self.record.lines), 10)

        # test scoping invalid segment
        with self.assertRaises(NidabaRecordException):
            self.record.scope_segment('foo')

        # test scoping valid segment inside current line
        self.record.scope_segment('seg_1')
        self.assertEqual(self.record.segment_scope, 'seg_1')
      
        # test segment scope also updates line scope
        self.record.scope_line('line_8')
        self.record.scope_segment('seg_1')
        self.assertEqual(self.record.line_scope, 'line_2')

        # test adding graphemes beneath segment
        self.record.add_graphemes([{'bbox': (0, 0, 0, 0), 
                               'confidence': 95,
                               'grapheme': x} for x in itertools.permutations('ABCD', 2)])
        self.assertEqual(len(self.record.segments[self.record.segment_scope]['content']),
                         len(list(itertools.permutations('ABCD', 2))))
        
        # test adding alternatives to lines
        self.record.add_choices('line_3', [{'confidence': 95,
                                       'alternative': x} for x in itertools.permutations('ABCD', 2)])
        self.assertEqual(len(self.record.lines['line_3']['alternatives']['content']),
                         len(list(itertools.permutations('ABCD', 2))))

        # test adding alternatives to segments
        self.record.add_choices('seg_1', [{'confidence': 95,
                                       'alternative': x} for x in itertools.permutations('ABCD', 2)])
        self.assertEqual(len(self.record.segments['seg_1']['alternatives']['content']),
                         len(list(itertools.permutations('ABCD', 2))))

        # test adding alternatives to graphemes
        self.record.add_choices('grapheme_1', [{'confidence': 95,
                                           'alternative': x} for x in itertools.permutations('ABCD', 2)])
        self.assertEqual(len(self.record.graphemes['grapheme_1']['alternatives']['content']),
                         len(list(itertools.permutations('ABCD', 2))))

        # test resetting scopes
        self.record.reset_line_scope()
        self.assertIsNone(self.record.line_scope)
        self.assertIsNone(self.record.segment_scope)

        self.record.scope_segment('seg_1')
        self.record.reset_segment_scope()
        self.assertIsNotNone(self.record.line_scope)
        self.assertIsNone(self.record.segment_scope)

        # test clearing segments
        self.record.clear_segments()
        self.assertEqual(len(self.record.segments), 0)

        # test clearing lines
        self.record.clear_lines()
        self.assertEqual(len(self.record.lines), 0)

    def test_respstmt(self):
        """
        Tests responsibility statement methods.
        """
        self.record = tei.OCRRecord()

        # test adding responsibility statements
        id_1 = self.record.add_respstmt('bar', 'foo')
        id = self.record.add_respstmt('foo', 'bar')
        self.assertEqual(2, len(self.record.respstmt))
        self.assertIn(id, self.record.respstmt)
        self.assertEqual(id, self.record.resp_scope)

        # test scoping invalid responsibility statements
        with self.assertRaises(NidabaRecordException):
            self.record.scope_respstmt('foo')

        # test scoping valid responsibility statements
        self.record.scope_respstmt(id_1)
        self.assertEqual(id_1, self.record.resp_scope)

        # test respstmt is added to elements
        for x in range(0, 10):
            self.record.add_line((0, 0, 0, 0))
        for x in range(0, 10):
            self.record.add_segment((0, 0, 0, 0), language='foo', confidence=80)
        self.record.add_graphemes([{'bbox': (0, 0, 0, 0), 
                               'confidence': 95,
                               'grapheme': x} for x in itertools.permutations('ABCD', 2)])
        self.record.add_choices('seg_1', [{'confidence': 95,
                                       'alternative': x} for x in itertools.permutations('ABCD', 2)])
        self.assertEqual(id_1, self.record.lines['line_3']['resp'])
        self.assertEqual(id_1, self.record.segments['seg_8']['resp'])
        self.assertEqual(id_1, self.record.graphemes['grapheme_5']['resp'])
     
        # test resetting responsibility scope
        self.record.reset_respstmt_scope()
        self.assertIsNone(self.record.resp_scope)

    def test_meta(self):
        """
        Test metadata methods.
        """
        self.record = tei.OCRRecord()

        # test that the document field
        for x in self.record.fields:
            setattr(self.record, x, uuid.uuid4())
        for x in self.record.fields:
            self.assertIsNotNone(getattr(self.record, x))

    def test_tei(self):
        """
        Test TEI de-/serialization.
        """
        fp = StringIO.StringIO()

        self.record.write_tei(fp)

        doc = etree.fromstring(fp.getvalue())
        
        # responsibility statements
        self.assertEqual(len(doc.findall('.//{}respStmt'.format(self.record.tei_ns))), 2)

        # number of lines, segments and graphemes
        lines = doc.findall('.//{}line'.format(self.record.tei_ns))
        segments = doc.findall('.//{}zone[@type="segment"]'.format(self.record.tei_ns))
        graphemes = doc.findall('.//{}zone[@type="grapheme"]'.format(self.record.tei_ns))

        self.assertEqual(len(lines), 11)
        self.assertEqual(len(lines[-2].findall('.//{}zone[@type="segment"]'.format(self.record.tei_ns))), 10)
        self.assertEqual(len(segments), 11)
        self.assertEqual(len(segments[-2].findall('.//{}zone[@type="grapheme"]'.format(self.record.tei_ns))),
                         len(list(itertools.permutations('ABCD', 2))))
        self.assertEqual(len(graphemes), 1+len(list(itertools.permutations('ABCD', 2))))

        for x in lines[:-1]:
            self.assertIsNotNone(x.get('resp'))
        for x in segments[:-1]:
            self.assertIsNotNone(x.get('resp'))
        for x in graphemes[:-1]:
            self.assertIsNotNone(x.get('resp'))

        self.assertIsNone(lines[-1].get('resp'))
        self.assertIsNone(segments[-1].get('resp'))
        self.assertIsNone(graphemes[-1].get('resp'))

        # check that confidence values are preserverd correctly
        self.assertEqual(len(doc.findall('.//{}certainty[@degree="0.95"]'.format(self.record.tei_ns))), 61)

        # choices on lines, segments and graphemes
        choices = doc.findall('.//{}choice'.format(self.record.tei_ns))
        self.assertEqual(len(choices), 4)
        self.assertIsNotNone(choices[0].find('{0}sic/{0}line[@{1}id="line_3"]'.format(self.record.tei_ns, self.record.xml_ns)))
        self.assertIsNotNone(choices[1].find('{0}sic/{0}zone[@{1}id="seg_1"]'.format(self.record.tei_ns, self.record.xml_ns)))
        self.assertIsNotNone(choices[2].find('{0}sic/{0}zone[@{1}id="grapheme_1"]'.format(self.record.tei_ns, self.record.xml_ns)))
        self.assertIsNotNone(choices[3].find('{0}sic/{0}line[@{1}id="line_11"]'.format(self.record.tei_ns, self.record.xml_ns)))

        self.assertEqual(len(choices[0].findall('{0}corr'.format(self.record.tei_ns))), 
                         len(list(itertools.permutations('ABCD', 2))))
        self.assertEqual(len(choices[1].findall('{0}corr'.format(self.record.tei_ns))), 
                         len(list(itertools.permutations('ABCD', 2))))
        self.assertEqual(len(choices[2].findall('{0}corr'.format(self.record.tei_ns))), 
                         len(list(itertools.permutations('ABCD', 2))))
        self.assertEqual(len(choices[3].findall('{0}corr'.format(self.record.tei_ns))), 
                         len(list(itertools.permutations('ABCD', 2))))

        # check that the loaded self.record is the same
        self.record2 = tei.OCRRecord()
        fp.seek(0)
        self.record2.load_tei(fp)
        #self.assertEqual(record2, self.record)

    def test_hocr(self):
        """
        Test hOCR de-/serialization.
        """
        fp = StringIO.StringIO()
        self.record.write_hocr(fp)

        doc = etree.HTML(fp.getvalue())
        
        lines = doc.findall('.//span[@class="ocr_line"]')
        segments = doc.findall('.//span[@class="ocrx_word"]')

        self.assertEqual(len(lines), 11)
        self.assertEqual(len(lines[-2].findall('.//span[@class="ocrx_word"]')), 10)
        self.assertEqual(len(segments), 11)
        self.assertEqual(len(''.join(segments[-2].itertext())),
                         2*len(list(itertools.permutations('ABCD', 2))))

        # choices on lines, segments. check grapheme choices are discarded
        choices = doc.findall('.//span[@class="alternatives"]')
        self.assertEqual(len(choices), 3)

        self.assertEqual(len(choices[0].findall('del')),
                         len(list(itertools.permutations('ABCD', 2))))
        self.assertEqual(len(choices[1].findall('del')),
                         len(list(itertools.permutations('ABCD', 2))))
        self.assertEqual(len(choices[2].findall('del')),
                         len(list(itertools.permutations('ABCD', 2))))

        # check that the loaded self.record is "same-ish". Multi-codepoint graphemes
        # unfortunately can't be encoded using hOCR.
        record2 = tei.OCRRecord()
        fp.seek(0)
        record2.load_hocr(fp)
        self.assertEqual(self.record.dimensions, record2.dimensions)
        self.assertEqual(self.record.img, record2.img)
        self.assertEqual(len(self.record.lines), len(record2.lines))
        self.assertEqual(len(self.record.segments), len(record2.segments))

    def test_text(self):
        """
        Test text serialization.
        """
        fp = StringIO.StringIO()
        # test metadata header is written
        self.record.write_text(fp)
        self.assertIn('+++', fp.getvalue())
        # test metadata header is NOT written
        fp = StringIO.StringIO()
        self.record.write_text(fp, header=False)
        self.assertNotIn('+++', fp.getvalue())

    def test_abbyyxml(self):
        """
        Test abbyyXML serialization.
        """
        fp = StringIO.StringIO()
	self.record.write_abbyyxml(fp)

        doc = etree.fromstring(fp.getvalue())
        g = doc.findall('.//{}charParams'.format(self.record.abbyy_ns))
        for x in g:
            self.assertEqual(x.get('charConfidence'), '95')
        # check number of graphemes match
        self.assertEqual(len(g),  13)
        # check that segments are converted to wordStart attributes
        self.assertEqual(len(doc.findall('.//{}charParams[@wordStart="true"]'.format(self.record.abbyy_ns))), 2)

    def test_alto(self):
        """
        Test ALTO de-/serialization.
        """
        fp = StringIO.StringIO()
        id = self.record.add_respstmt('recognition', 'baz')
        self.record.write_alto(fp)
        doc = etree.fromstring(fp.getvalue())
       
    def test_validate_alto(self):
        """
        Validate ALTO 
        """
        fp = StringIO.StringIO()
        id = self.record.add_respstmt('recognition', 'baz')
        self.record.add_segment((0, 0, 0, 0), language='foo', confidence=80)
        self.record.add_graphemes([{'bbox': (0, 0, 0, 0), 
                               'confidence': 95,
                               'grapheme': ' '}])
        self.record.add_segment((0, 0, 0, 0), language='foo', confidence=80)
        self.record.add_graphemes([{'bbox': (0, 0, 0, 0), 
                               'confidence': 95,
                               'grapheme': 'AB'}])
        self.record.add_choices('line_11', [{'confidence': 95,
                                           'alternative': ''.join(x)} for x in itertools.permutations('ABCD', 2)])
        self.record.write_alto(fp)
        doc = etree.fromstring(fp.getvalue())
        with open(os.path.join(resources, 'alto-3-1.xsd')) as schema_fp:
            alto_schema = etree.XMLSchema(etree.parse(schema_fp))
            alto_schema.assertValid(doc)

    def test_validate_abbyyxml(self):
        fp = StringIO.StringIO()
        id = self.record.add_respstmt('recognition', 'baz')
        self.record.write_abbyyxml(fp)
        doc = etree.fromstring(fp.getvalue())

        with open(os.path.join(resources, 'FineReader10-schema-v1.xml')) as schema_fp:
            alto_schema = etree.XMLSchema(etree.parse(schema_fp))
            alto_schema.assertValid(doc)

    # the schema is broken for some reason
    @unittest.expectedFailure
    def test_validate_tei(self):
        fp = StringIO.StringIO()
        id = self.record.add_respstmt('recognition', 'baz')
        self.record.write_tei(fp)
        doc = etree.fromstring(fp.getvalue())

        with open(os.path.join(resources, 'tei_ocr.rng')) as schema_fp:
            tei_schema = etree.RelaxNG(etree.parse(schema_fp))
            tei_schema.assertValid(doc)

if __name__ == '__main__':
    unittest.main()
