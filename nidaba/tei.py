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

from nidaba.nidabaexceptions import NidabaTEIException


def max_bbox(boxes):
    """
    Calculates the minimal bounding box containing all boxes contained in an
    iterator.

    Args:
        boxes (iterator): An iterator returning tuples of the format (x0, y0,
                          x1, y1)
    Returns:
        A box covering all bounding boxes in the input argument
    """
    sbox = list(map(sorted, list(zip(*boxes))))
    return (sbox[0][0], sbox[1][0], sbox[2][-1], sbox[3][-1])


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
        header = SubElement(doc, 'teiHeader')
        fileDesc = SubElement(header, 'fileDesc')
        SubElement(fileDesc, 'titleStmt')
        SubElement(fileDesc, 'publicationStmt')

        self.word_scope = None
        self.line_scope = None
        self.line_cnt = -1
        self.seg_cnt = -1
        self.grapheme_cnt = -1
        self.doc = doc

    def document(self, dim, image_url):
        sourceDoc = SubElement(self.doc, 'sourceDoc')
        surface = SubElement(sourceDoc, 'surface', ulx='0', uly='0',
                             lrx=str(dim[0]), lry=str(dim[1]))
        SubElement(surface, 'graphic', url=image_url)
        SubElement(surface, 'zone')

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
        title = self.doc.find('//' + self.tei_ns + 'teiHeader//' + self.tei_ns
                              + 'title')
        if hasattr(title, 'text'):
            return title.text
        else:
            return None

    @title.setter
    def title(self, value):
        title = self.doc.find('//' + self.tei_ns + 'teiHeader//' + self.tei_ns
                              + 'title')
        if not title:
            title = SubElement(self.doc.find('//' + self.tei_ns + 'titleStmt'),
                               'title')
        title.text = value

    @property
    def authority(self):
        authority = self.doc.find('//' + self.tei_ns + 'teiHeader//' +
                                  self.tei_ns + 'authority')
        if hasattr(authority, 'text'):
            return authority.text
        else:
            return None

    @authority.setter
    def authority(self, value):
        authority = self.doc.find('//' + self.tei_ns + 'teiHeader//' +
                                  self.tei_ns + 'title')
        if not authority:
            authority = SubElement(self.doc.find('//' + self.tei_ns +
                                                 'publicationStmt'),
                                   'authority')
        authority.text = value

    @property
    def sourceDesc(self):
        sourceDesc = self.doc.find('//' + self.tei_ns + 'teiHeader//' +
                                   self.tei_ns + 'sourceDesc')
        if hasattr(sourceDesc, 'text'):
            return sourceDesc.text
        else:
            return None

    @sourceDesc.setter
    def sourceDesc(self, value):
        sourceDesc = self.doc.find('//' + self.tei_ns + 'teiHeader//' +
                                   self.tei_ns + 'sourceDesc')
        if not sourceDesc:
            sourceDesc = SubElement(self.doc.find('//' + self.tei_ns +
                                    'fileDesc'), 'sourceDesc')
        sourceDesc.text = value

    @property
    def license(self):
        license = self.doc.find('//' + self.tei_ns + 'teiHeader//' +
                                self.tei_ns + 'licence')
        if hasattr(license, 'text'):
            return license.text
        else:
            return None

    @license.setter
    def license(self, value):
        license = self.doc.find('//' + self.tei_ns + 'teiHeader//' +
                                self.tei_ns + 'licence')
        if not license:
            avail = SubElement(self.doc.find('//' + self.tei_ns +
                               'publicationStmt'), 'availability')
            license = SubElement(avail, 'licence')
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
        id = 0
        for resp in self.doc.iter(self.tei_ns + 'respStmt'):
            id += 1
        r = SubElement(self.doc.find('//' + self.tei_ns + 'titleStmt'),
                       'respStmt')
        r.set(self.xml_ns + 'id', u'resp_' + unicode(id + 1))
        self.resp = r.get(self.xml_ns + 'id')
        SubElement(r, 'resp').text = resp
        SubElement(r, 'name').text = name
        return r.get(self.xml_ns + 'id')

    def scope_respstmt(self, id):
        """
        Scopes a respStmt for subsequent addition of graphemes/segments.

        Args:
            id (unicode): XML id of the responsibility statement

        Raises:
            NidabaTEIException if the identifier is unknown
        """
        if not self.doc.find("//" + self.tei_ns + "respStmt[@" + self.xml_ns +
                             "id='" + id + "']"):
            raise NidabaTEIException('No such responsibility statement.')
        self.resp = id

    @property
    def lines(self):
        """
        Returns an reading order sorted list of tuples in the format (x0, y0,
        x1, y1, text).
        """
        lines = []
        for line in self.doc.iter(self.tei_ns + 'line'):
            text = ''.join(line.itertext())
            lines.append((line.get('ulx'), line.get('uly'), line.get('lrx'),
                          line.get('lry'), text))
        return lines

    def add_line(self, dim):
        """
        Marks the beginning of a new topographical line and scopes it.

        Args:
            dim (tuple): A tuple containing the bounding box (x0, y0, x1, y1)
        """
        zone = self.doc.find('//' + self.tei_ns + 'zone')
        self.line_scope = SubElement(zone, 'line', ulx=str(dim[0]),
                                     uly=str(dim[1]), lrx=str(dim[2]),
                                     lry=str(dim[3]))
        self.line_cnt += 1
        self.line_scope.set(self.xml_ns + 'id', 'line_' + str(self.line_cnt))
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
        line = self.doc.find("//" + self.tei_ns + "line[@" + self.xml_ns +
                             "id='" + id + "']")
        if not line:
            raise NidabaTEIException('No such line')
        self.line_scope = line

    @property
    def segments(self):
        """
        Returns an reading order sorted list of tuples in the format (x0, y0,
        x1, y1, text).
        """
        segments = []
        for seg in self.doc.iter(self.tei_ns + 'seg'):
            text = ''.join(seg.itertext())
            segments.append((seg.get('ulx'), seg.get('uly'), seg.get('lrx'),
                             seg.get('lry'), text))
        return segments

    def add_segment(self, dim):
        """
        Marks the beginning of a new topographical segment in the current
        scope. Most often this correspond to a word recognized by an engine.

        Args:
            dim (tuple): A tuple containing the bounding box (x0, y0, x1, y1)
        """
        zone = SubElement(self.line_scope, 'zone', ulx=str(dim[0]),
                          uly=str(dim[1]), lrx=str(dim[2]), lry=str(dim[3]),
                          type='word')
        self.word_scope = SubElement(zone, 'seg')
        self.seg_cnt += 1
        self.word_scope.attrib[self.xml_ns + 'id'] = 'seg_' + str(self.seg_cnt)

    @property
    def graphemes(self):
        """
        Returns a reading order sorted list of tuples in the format (x0, y0,
        x1, y1, text).
        """
        graphemes = []
        for g in self.doc.iter(self.tei_ns + 'g'):
            text = ''.join(g.itertext())
            graphemes.append((g.getparent().get('ulx'),
                              g.getparent().get('uly'),
                              g.getparent().get('lrx'),
                              g.getparent().get('lry'), text))
        return graphemes

    def add_graphemes(self, it):
        """
        Adds a number of graphemes to the current scope (either line or word).
        A line or segment has to be created beforehand.

        Args:
            it (iterable): An iterable returning a tuple containing a glyph
            (unicode), and optionally the bounding box of this glyph (x0, y0,
            x1, y1) and a recognition confidence value in the range 0 and 1.
        """
        scope = self.word_scope if self.word_scope else self.line_scope
        for t in it:
            if len(t) == 1:
                g = t
                zone = scope
            else:
                conf = None
                if len(t) == 2:
                    g, box = t
                else:
                    g, box, conf = t
                ulx, uly, lrx, lry = box
                zone = SubElement(scope, 'zone', ulx=str(ulx), uly=str(uly),
                                  lrx=str(lrx), lry=str(lry), type='grapheme')
                if conf:
                    cert = SubElement(zone, 'certainty',
                                      degree=u'{0:.2f}'.format(conf))
                    if self.resp:
                        cert.attrib['resp'] = '#' + self.resp
            glyph = SubElement(zone, 'g')
            self.grapheme_cnt += 1
            glyph.set(self.xml_ns + 'id', 'grapheme_' + str(self.grapheme_cnt))
            glyph.text = g
            if self.resp:
                glyph.attrib['resp'] = '#' + self.resp

    def clear_graphemes(self):
        """
        Deletes all <g> nodes from the document. Mainly used when combining
        page segmentation algorithms extracting graphemes and OCR engines
        operating on lexemes. Also resets the current scope to the first line
        (and if applicable its first segment).
        """
        for zone in self.doc.iterfind('//' + self.tei_ns +
                                      "zone[@type='glyph']"):
            zone.getparent().remove(zone)
        self.word_scope = self.doc.find('//' + self.tei_ns + 'seg')
        self.line_scope = self.doc.find('//' + self.tei_ns + 'line')

    def clear_segments(self):
        """
        Deletes all <seg> nodes from the document. Mainly used when combining
        page segmentation algorithms extracting lexemes (and graphemes) and OCR
        engines operating on lines. Also resets the current scope to the first
        line.
        """
        for zone in self.doc.iterfind('//' + self.tei_ns +
                                      "zone[@type='word']"):
            zone.getparent().remove(zone)
        self.line_scope = self.doc.find('//' + self.tei_ns + 'line')

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
        self.doc = etree.parse(fp)
        self.line_cnt = len(list(self.doc.iter(self.tei_ns + 'line'))) - 1
        self.seg_cnt = len(list(self.doc.iter(self.tei_ns + 'seg'))) - 1
        self.grapheme_cnt = len(list(self.doc.iter(self.tei_ns + 'g'))) - 1
