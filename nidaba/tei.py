# -*- coding: utf-8 -*-
"""
nidaba.tei
~~~~~~~~~~

A module for interfacing TEI OCR output
"""

from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

from lxml import etree
from lxml.etree import Element, SubElement

from collections import OrderedDict
from copy import deepcopy

from nidaba.nidabaexceptions import NidabaTEIException


def _parse_hocr(title):
    """
    Parses the hOCR title string and returns a dictionary containing its
    contents.
    """
    def int_float_or_str(s):
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                try:
                    return unicode(s)
                except UnicodeDecodeError:
                    return s

    out = {}
    props = [x.strip() for x in title.split(';')]
    for prop in props:
        p = prop.split()
        out[p[0]] = tuple(int_float_or_str(x) for x in p[1:])
    return out


class TEIFacsimile(object):

    xml_ns = '{http://www.w3.org/XML/1998/namespace}'
    tei_ns = '{http://www.tei-c.org/ns/1.0}'

    """
    A class encapsulating a TEI XML document following the TEI digital
    facsimile guidelines for embedded transcriptions.
    """
    def __init__(self):
        doc = Element('TEI', nsmap={None: 'http://www.tei-c.org/ns/1.0'},
                      version='5.0')
        header = SubElement(doc, self.tei_ns + 'teiHeader')
        fileDesc = SubElement(header, self.tei_ns + 'fileDesc')
        SubElement(fileDesc, self.tei_ns + 'titleStmt')
        SubElement(fileDesc, self.tei_ns + 'publicationStmt')

        self.word_scope = None
        self.line_scope = None
        self.resp = None
        self.line_cnt = -1
        self.seg_cnt = -1
        self.grapheme_cnt = -1
        self.doc = doc

    def document(self, dim, image_url):
        sourceDoc = SubElement(self.doc, self.tei_ns + 'sourceDoc')
        surface = SubElement(sourceDoc, self.tei_ns + 'surface', ulx='0',
                             uly='0', lrx=str(dim[0]), lry=str(dim[1]))
        SubElement(surface, self.tei_ns + 'graphic', url=image_url)
        SubElement(surface, self.tei_ns + 'zone')

    @property
    def description(self):
        """
        Returns a tuple containing a source document's path and its dimensions.
        """
        surface = self.doc.find('//' + self.tei_ns + 'sourceDoc/' + self.tei_ns
                                + 'surface')
        return (surface.get('ulx'),
                surface.get('uly'),
                surface.get('lrx'),
                surface.get('lry'),
                surface.find(self.tei_ns + 'graphic').get('url'))

    @property
    def title(self):
        title = self.doc.find('.//' + self.tei_ns + 'teiHeader//' + self.tei_ns + 'title')
        if hasattr(title, 'text'):
            return title.text
        else:
            return None

    @title.setter
    def title(self, value):
        title = self.doc.find('.//' + self.tei_ns + 'teiHeader//' + self.tei_ns
                              + 'title')
        if title is None:
            title = SubElement(self.doc.find('.//' + self.tei_ns + 'titleStmt'),
                               self.tei_ns + 'title')
        title.text = value

    @property
    def authority(self):
        authority = self.doc.find('.//' + self.tei_ns + 'teiHeader//' +
                                  self.tei_ns + 'authority')
        if hasattr(authority, 'text'):
            return authority.text
        else:
            return None

    @authority.setter
    def authority(self, value):
        authority = self.doc.find('.//' + self.tei_ns + 'teiHeader//' +
                                  self.tei_ns + 'title')
        if authority is None:
            authority = SubElement(self.doc.find('//' + self.tei_ns +
                                                 'publicationStmt'),
                                   self.tei_ns + 'authority')
        authority.text = value

    @property
    def sourceDesc(self):
        sourceDesc = self.doc.find('.//' + self.tei_ns + 'teiHeader//' +
                                   self.tei_ns + 'sourceDesc')
        if hasattr(sourceDesc, 'text'):
            return sourceDesc.text
        else:
            return None

    @sourceDesc.setter
    def sourceDesc(self, value):
        sourceDesc = self.doc.find('.//' + self.tei_ns + 'teiHeader//' +
                                   self.tei_ns + 'sourceDesc')
        if sourceDesc is None:
            sourceDesc = SubElement(self.doc.find('//' + self.tei_ns +
                                    'fileDesc'), self.tei_ns + 'sourceDesc')
        sourceDesc.text = value

    @property
    def license(self):
        license = self.doc.find('.//' + self.tei_ns + 'teiHeader//' +
                                self.tei_ns + 'licence')
        if hasattr(license, 'text'):
            return license.text
        else:
            return None

    @license.setter
    def license(self, value):
        license = self.doc.find('.//' + self.tei_ns + 'teiHeader//' +
                                self.tei_ns + 'licence')
        if license is None:
            avail = SubElement(self.doc.find('//' + self.tei_ns +
                               'publicationStmt'), self.tei_ns +
                               'availability')
            license = SubElement(avail, self.tei_ns + 'licence')
        license.text = value

    @property
    def respstmt(self):
        """
        Returns an ordered dictionary of responsibility statements from the XML
        document.
        """
        d = OrderedDict()
        for resp in self.doc.iter(self.tei_ns + 'respStmt'):
            rip = resp.get(self.xml_ns + 'id')
            d[rip] = {c.tag: c.text for c in resp.getchildren()}
        return d

    def add_respstmt(self, name, resp):
        """
        Adds a responsibility statement and treats all subsequently added text
        as a responsibility of this statement.

        Args:
            name (unicode): Identifier of the process that generated the
                            output.
            resp (unicode): Phrase describing the nature of the process
                            generating the output.

        Returns:
            A unicode string corresponding to the responsibility identifier.
        """
        id = -1
        for rstmt in self.doc.iter(self.tei_ns + 'respStmt'):
            id += 1
        r = SubElement(self.doc.find('.//' + self.tei_ns + 'titleStmt'),
                       self.tei_ns + 'respStmt')
        r.set(self.xml_ns + 'id', u'resp_' + unicode(id + 1))
        self.resp = r.get(self.xml_ns + 'id')
        SubElement(r, self.tei_ns + 'resp').text = resp
        SubElement(r, self.tei_ns + 'name').text = name
        return r.get(self.xml_ns + 'id')

    def scope_respstmt(self, id):
        """
        Scopes a respStmt for subsequent addition of graphemes/segments.

        Args:
            id (unicode): XML id of the responsibility statement

        Raises:
            NidabaTEIException if the identifier is unknown
        """
        if self.doc.find(".//" + self.tei_ns + "respStmt[@" + self.xml_ns +
                         "id='" + id + "']") is None:
            raise NidabaTEIException('No such responsibility statement.')
        self.resp = id

    @property
    def lines(self):
        """
        Returns an reading order sorted list of tuples in the format (x0, y0,
        x1, y1, xml id, text).
        """
        lines = []
        for line in self.doc.iter(self.tei_ns + 'line'):
            text = ''.join(line.itertext())
            lines.append((line.get('ulx'), line.get('uly'), line.get('lrx'),
                          line.get('lry'), line.get(self.xml_ns + 'id'), text))
        return lines

    def add_line(self, dim):
        """
        Marks the beginning of a new topographical line and scopes it.

        Args:
            dim (tuple): A tuple containing the bounding box (x0, y0, x1, y1)
        """
        zone = self.doc.find('.//' + self.tei_ns + 'zone')
        self.line_scope = SubElement(zone, self.tei_ns + 'line',
                                     ulx=str(dim[0]), uly=str(dim[1]),
                                     lrx=str(dim[2]), lry=str(dim[3]))
        self.line_cnt += 1
        self.line_scope.set(self.xml_ns + 'id', 'line_' + str(self.line_cnt))
        if self.resp:
            self.line_scope.set('resp', '#' + self.resp)
        self.word_scope = None

    def scope_line(self, id):
        """
        Scopes a particular line for addition of segments/graphemes. Also
        disables the current segment scope.

        Args:
            id (unicode): XML id of the line tag

        Raises:
            NidabaTEIException if the identifier is unknown
        """
        line = self.doc.find(".//" + self.tei_ns + "line[@" + self.xml_ns +
                             "id='" + id + "']")
        if line is None:
            raise NidabaTEIException('No such line')
        self.line_scope = line

    @property
    def segments(self):
        """
        Returns an reading order sorted list of tuples in the format (x0, y0,
        x1, y1, id, text).
        """
        segments = []
        for seg in self.doc.iter(self.tei_ns + 'seg'):
            text = ''.join(seg.itertext())
            if seg.getparent().get('type') == 'word':
                bbox = (seg.getparent().get('ulx'),
                        seg.getparent().get('uly'),
                        seg.getparent().get('lrx'),
                        seg.getparent().get('lry'))
            else:
                bbox = (None, None, None, None)
            segments.append(bbox + (seg.get(self.xml_ns + 'id'), text))
        return segments

    def add_segment(self, dim, lang=None, confidence=None):
        """
        Marks the beginning of a new topographical segment in the current
        scope. Most often this correspond to a word recognized by an engine.

        Args:
            dim (tuple): A tuple containing the bounding box (x0, y0, x1, y1)
            lang (unicode): Optional identifier of the segment language.
            confidence (float): Optional confidence value between 0 and 100.
        """
        zone = SubElement(self.line_scope, self.tei_ns + 'zone', 
                          ulx=str(dim[0]), uly=str(dim[1]), lrx=str(dim[2]),
                          lry=str(dim[3]), type='word')
        self.word_scope = SubElement(zone, self.tei_ns + 'seg')
        self.seg_cnt += 1
        self.word_scope.set(self.xml_ns + 'id', 'seg_' + str(self.seg_cnt))
        if confidence:
            cert = SubElement(self.word_scope, self.tei_ns + 'certainty',
                              degree = u'{0:.2f}'.format(confidence/100.0),
                              locus = 'value',
                              target = '#' + 'seg_' + str(self.seg_cnt))
            if self.resp:
                cert.set('resp', '#' + self.resp)
        if self.resp:
            self.word_scope.set('resp', '#' + self.resp)

    def clear_segment(self):
        """
        Marks the end of the current topographical segment.
        """
        self.word_scope = None

    @property
    def graphemes(self):
        """
        Returns a reading order sorted list of tuples in the format (x0, y0,
        x1, y1, id, text).
        """
        graphemes = []
        for g in self.doc.iter(self.tei_ns + 'g'):
            text = ''.join(g.itertext())
            if g.getparent().get('type') == 'grapheme':
                bbox = (g.getparent().get('ulx'),
                        g.getparent().get('uly'),
                        g.getparent().get('lrx'),
                        g.getparent().get('lry'))
            else:
                bbox = (None, None, None, None)
            graphemes.append(bbox + (g.get(self.xml_ns + 'id'), text))
        return graphemes

    def add_graphemes(self, it):
        """
        Adds a number of graphemes to the current scope (either line or word).
        A line or segment has to be created beforehand.

        Args:
            it (iterable): An iterable returning a tuple containing a glyph
                           (unicode), and optionally the bounding box of this
                           glyph (x0, y0, x1, y1) and a recognition confidence
                           value in the range 0 and 100.
        """
        scope = self.word_scope if self.word_scope is not None else self.line_scope
        for t in it:
            conf = None
            if len(t) == 1:
                g = t
                zone = scope
            else:
                if len(t) == 2:
                    g, box = t
                else:
                    g, box, conf = t
                ulx, uly, lrx, lry = box
                zone = SubElement(scope, self.tei_ns + 'zone', ulx=str(ulx),
                                  uly=str(uly), lrx=str(lrx), lry=str(lry),
                                  type='grapheme', resp= '#' + self.resp)
            glyph = SubElement(zone, self.tei_ns + 'g')
            self.grapheme_cnt += 1
            glyph.set(self.xml_ns + 'id', 'grapheme_' + str(self.grapheme_cnt))
            glyph.text = g
            if conf:
                cert = SubElement(zone, self.tei_ns + 'certainty',
                                  degree=u'{0:.2f}'.format(conf/100.0),
                                  locus = 'value',
                                  target = '#' + 'grapheme_' +
                                  str(self.grapheme_cnt))
                if self.resp:
                    cert.set('resp', '#' + self.resp)
            if self.resp:
                glyph.set('resp', '#' + self.resp)
    
    def add_choices(self, id, it):
        """
        Adds alternative interpretations to an element.

        Args:
            id (unicode): 
            it (iterable): An iterable returning a tuple containing an
                           alternative reading and an optional confidence value
                           in the range between 0 and 100.
        """
        el = self.doc.xpath("//*[@xml:id=$tagid]", tagid = id)[0]
        sic = deepcopy(el)
        # remove old tree
        parent = el.getparent()
        parent.remove(el)
        choice = SubElement(parent, self.tei_ns + 'choice')
        # reinsert beneath sic element
        SubElement(choice, self.tei_ns + 'sic').append(sic)
        for alt in it:
            corr = SubElement(choice, self.tei_ns + 'corr')
            if self.resp:
                corr.set('resp', '#' + self.resp)
            corr.text = alt[0]
            if len(alt) == 2:
                cert = SubElement(corr, self.tei_ns + 'certainty',
                                  degree = u'{0:.2f}'.format(alt[1]/100.0),
                                  locus = 'value')
                if self.resp:
                    cert.set('resp', '#' + self.resp)

    def clear_lines(self):
        """
        Deletes all <line> nodes from the document.
        """
        for zone in self.doc.iterfind('.//' + self.tei_ns +
                                      "line"):
            zone.getparent().remove(zone)
        self.line_scope = None
        self.word_scope = None
        self.line_cnt = -1
        self.seg_cnt = -1
        self.grapheme_cnt = -1

    def clear_graphemes(self):
        """
        Deletes all <g> nodes from the document. Mainly used when combining
        page segmentation algorithms extracting graphemes and OCR engines
        operating on lexemes. Also resets the current scope to the first line
        (and if applicable its first segment).
        """
        for zone in self.doc.iterfind('.//' + self.tei_ns +
                                      "zone[@type='grapheme']"):
            zone.getparent().remove(zone)
        self.line_scope = self.doc.find('.//' + self.tei_ns + 'line')
        self.word_scope = self.doc.find('.//' + self.tei_ns + 'seg')
        self.grapheme_cnt = -1

    def clear_segments(self):
        """
        Deletes all <seg> nodes from the document. Mainly used when combining
        page segmentation algorithms extracting lexemes (and graphemes) and OCR
        engines operating on lines. Also resets the current scope to the first
        line.
        """
        for zone in self.doc.iterfind('.//' + self.tei_ns +
                                      "zone[@type='word']"):
            zone.getparent().remove(zone)
        self.line_scope = self.doc.find('.//' + self.tei_ns + 'line')
        self.word_scope = None
        self.seg_cnt = -1
        self.grapheme_cnt = -1

    def load_hocr(self, fp):
        """
        Extracts as much information as possible from an hOCR file and converts
        it to TEI.

        TODO: Write a robust XSL transformation.

        Args:
            fp (file): File descriptor to read data from.
        """
        doc = etree.HTML(fp.read())
        self.clear_lines()
        self.clear_segments()
        self.clear_graphemes()
        el = doc.find(".//meta[@name='ocr-system']")
        if el is not None:
            self.add_respstmt(el.get('content'), 'ocr-system')
        page = doc.find('.//div[@class="ocr_page"]')
        o = _parse_hocr(page.get('title'))
        self.document(o['bbox'], o['image'][0])
        for line in doc.iterfind('.//span[@class="ocr_line"]'):
            self.add_line(_parse_hocr(line.get('title'))['bbox'])
            if not line.xpath('.//span[starts-with(@class, "ocrx")]'):
                self.add_graphemes(''.join(line.itertext()))
            for span in line.xpath('.//span[starts-with(@class, "ocrx")]'):
                o = _parse_hocr(span.get('title'))
                confidence = None
                bbox = None
                if 'bbox' in o:
                    bbox = o['bbox']
                if 'x_wconf' in o:
                    confidence = int(o['x_wconf'][0])/100.0
                self.add_segment(bbox, confidence=confidence)
                self.add_graphemes(''.join(span.itertext()))
                if span.tail:
                    self.clear_segment()
                    self.add_graphemes(span.tail)

    def write_hocr(fp):
        """
        Writes the TEI document as an hOCR file.

        Args:
            fp (file): File descriptor to write to.
        """
        pass

    def write(self, fp):
        """
        Writes the TEI XML document to a file object.

        Args:
            fp (file): file object to write to
        """
        fp.write(etree.tounicode(self.doc).encode('utf-8'))

    def read(self, fp):
        """
        Reads an XML document from a file object and populates all recognized
        attributes. Also sets the scope to the first line (and if applicable
        segment) of the document.

        Args:
            fp (file): file object to read from
        """
        self.doc = etree.parse(fp).getroot()
        self.line_cnt = len(list(self.doc.iter(self.tei_ns + 'line'))) - 1
        self.seg_cnt = len(list(self.doc.iter(self.tei_ns + 'seg'))) - 1
        self.grapheme_cnt = len(list(self.doc.iter(self.tei_ns + 'g'))) - 1
