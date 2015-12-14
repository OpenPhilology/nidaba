# -*- coding: utf-8 -*-
"""
nidaba.tei
~~~~~~~~~~

A module for interfacing TEI OCR output
"""

from __future__ import absolute_import, division, print_function

from lxml import etree
from lxml.etree import Element, SubElement

from collections import OrderedDict
from functools import partial
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
    """
    A class encapsulating a TEI XML document following the TEI digital
    facsimile guidelines for embedded transcriptions.
    """

    xml_ns = '{http://www.w3.org/XML/1998/namespace}'
    tei_ns = '{http://www.tei-c.org/ns/1.0}'

    # automatically generated properties in the fileDesc element and xpath to their location
    fields = OrderedDict([('title', ('titleStmt', '/{0}title'.format(tei_ns),)),
                          ('author', ('titleStmt', '/{0}author'.format(tei_ns),
                                      'ref')),
                          ('editor', ('titleStmt', '/{0}editor'.format(tei_ns),
                                      'ref')),
                          ('funder', ('titleStmt', '/{0}funder'.format(tei_ns),
                                      'ref')),
                          ('principal', ('titleStmt',
                                         '/{0}principal'.format(tei_ns),
                                         'ref')),
                          ('sponsor', ('titleStmt',
                                       '/{0}sponsor'.format(tei_ns), 'ref')),
                          ('meeting', ('titleStmt',
                                       '/{0}meeting'.format(tei_ns),
                                       'meeting')),
                          ('edition', ('editionStmt',
                                       '/{0}edition'.format(tei_ns),)),
                          ('publisher', ('publicationStmt',
                                         '/{0}publisher'.format(tei_ns),
                                         'target')),
                          ('distributor', ('publicationStmt',
                                           '/{0}distributor'.format(tei_ns),
                                           'target')),
                          ('authority', ('publicationStmt',
                                         '/{0}authority'.format(tei_ns),
                                         'target')),
                          ('idno', ('publicationStmt',
                                    '/{0}idno'.format(tei_ns), 'type')),
                          ('pub_place', ('publicationStmt',
                                         '/{0}pubPlace'.format(tei_ns),)),
                          ('licence', ('publicationStmt',
                                       '/{0}availability/{0}licence'.format(tei_ns),
                                       'target')),
                          ('series_title', ('seriesStmt',
                                            '/{0}p'.format(tei_ns),)),
                          ('note', ('notesStmt', '/{0}notes'.format(tei_ns),)),
                          ('source_desc', ('sourceDesc',
                                           '/{0}p'.format(tei_ns),))])

    fileDesc = ['titleStmt', 'editionStmt', 'publicationStmt', 'seriesStmt',
                'notesStmt', 'sourceDesc', ]

    def _generic_getter(self, field):
        el = self.doc.find('.//{0}teiHeader//{0}{1}{2}'.format(self.tei_ns,
                                                               self.fields[field][0],
                                                               self.fields[field][1]))
        if hasattr(el, 'text'):
            return el.text
        else:
            return None

    def _generic_setter(self, value, field):
        entry = self.fields[field]
        el = self.doc.find('.//{0}teiHeader//{0}{1}{2}'.format(self.tei_ns,
                                                               entry[0],
                                                               entry[1]))
        # create *Stmt in correct order
        parent = self.doc.find('.//{0}teiHeader//{0}{1}'.format(self.tei_ns, entry[0]))
        if parent is None:
            for loc in xrange(self.fileDesc.index(entry[0]), -1, -1):
                prev_stmt = self.doc.find('.//{0}{1}'.format(self.tei_ns, self.fileDesc[loc]))
                if prev_stmt is not None:
                    break
            parent = Element('{0}{1}'.format(self.tei_ns, entry[0]))
            prev_stmt.addnext(parent)
        # create all nodes along xpath in field[1]
        if el is None:
            el = parent
            for node in entry[1].split('/{')[1:]:
                el = SubElement(el, '{' + node)
        if isinstance(value, list):
            el.set(entry[2], value[1])
            value = value[0]
        el.text = value

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
    def lang(self):
        """
        The language value of the teiHeader
        """
        el = self.doc.find('.//' + self.tei_ns + 'teiHeader')
        if el is not None:
            return el.get(self.xml_ns + 'lang')
        return None

    @lang.setter
    def lang(self, value):
        el = self.doc.find('.//' + self.tei_ns + 'teiHeader')
        el.set(self.xml_ns + 'lang', value)

    @property
    def description(self):
        """
        Returns a tuple containing a source document's path and its dimensions.
        """
        surface = self.doc.find('//{0}sourceDoc/{0}surface'.format(self.tei_ns))
        return (surface.get('ulx'),
                surface.get('uly'),
                surface.get('lrx'),
                surface.get('lry'),
                surface.find(self.tei_ns + 'graphic').get('url'))

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
        if self.doc.find(".//{0}respStmt[@{1}id='{2}']".format(self.tei_ns,
                                                               self.xml_ns,
                                                               id)) is None:
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
            lines.append((int(line.get('ulx')), int(line.get('uly')),
                          int(line.get('lrx')), int(line.get('lry')),
                          line.get(self.xml_ns + 'id'), text))
        return lines

    def add_line(self, dim):
        """
        Marks the beginning of a new topographical line and scopes it.

        Args:
            dim (tuple): A tuple containing the bounding box (x0, y0, x1, y1)
        """
        surface_zone = self.doc.find('.//{0}surface/{0}zone'.format(self.tei_ns))
        self.line_scope = SubElement(surface_zone, self.tei_ns + 'line',
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
        x1, y1, confidence, id, text).
        """
        segments = []
        for seg in self.doc.iterfind('.//' + self.tei_ns + "zone[@type='segment']"):
            text = ''.join(seg.itertext())
            bbox = (int(seg.get('ulx')),
                    int(seg.get('uly')),
                    int(seg.get('lrx')),
                    int(seg.get('lry')))
            cert = self.doc.xpath("//*[local-name()='certainty' and @target=$tag]",
                                  tag='#' + seg.get(self.xml_ns + 'id'))
            if len(cert):
                cert = int(100.0 * float(cert[0].get('degree')))
            else:
                cert = None
            segments.append(bbox + (cert,) + (seg.get(self.xml_ns + 'id'), text))
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
                          lry=str(dim[3]), type='segment')
        self.word_scope = zone
        self.seg_cnt += 1
        self.word_scope.set(self.xml_ns + 'id', 'seg_' + str(self.seg_cnt))
        if confidence:
            cert = SubElement(self.word_scope, self.tei_ns + 'certainty',
                              degree=u'{0:.2f}'.format(confidence / 100.0),
                              locus='value',
                              target='#' + 'seg_' + str(self.seg_cnt))
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
            if g.getparent().getparent().get('type') == 'grapheme':
                bbox = (int(g.getparent().getparent().get('ulx')),
                        int(g.getparent().getparent().get('uly')),
                        int(g.getparent().getparent().get('lrx')),
                        int(g.getparent().getparent().get('lry')))
            else:
                bbox = (None, None, None, None)
            cert = self.doc.xpath("//*[local-name()='certainty' and @target=$tag]",
                                  tag='#' + g.get(self.xml_ns + 'id'))
            if len(cert):
                cert = int(100.0 * float(cert[0].get('degree')))
            else:
                cert = None
            graphemes.append(bbox + (cert,) + (g.get(self.xml_ns + 'id'), text))
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
                                  type='grapheme', resp='#' + self.resp)
            # insert <seg> before <g> as TEI forbids a <g> directly beneath a
            # <zone>
            glyph = SubElement(SubElement(zone, self.tei_ns + 'seg'),
                               self.tei_ns + 'g')
            self.grapheme_cnt += 1
            glyph.set(self.xml_ns + 'id', 'grapheme_' + str(self.grapheme_cnt))
            glyph.text = g
            if conf:
                cert = SubElement(zone, self.tei_ns + 'certainty',
                                  degree=u'{0:.2f}'.format(conf / 100.0),
                                  locus='value',
                                  target='#' + 'grapheme_' +
                                  str(self.grapheme_cnt))
                if self.resp:
                    cert.set('resp', '#' + self.resp)
            if self.resp:
                glyph.set('resp', '#' + self.resp)

    def add_choices(self, id, it):
        """
        Adds alternative interpretations to an element.

        Args:
            id (unicode): Globally unique XML id of the element.
            it (iterable): An iterable returning a tuple containing an
                           alternative reading and an optional confidence value
                           in the range between 0 and 100.
        """
        el = self.doc.xpath("//*[@xml:id=$tagid]", tagid=id)[0]
        # remove old tree only if not already part of an choice segment.
        parent = el.getparent()
        if parent.tag == self.tei_ns + 'sic':
            choice = parent.find('..')
        else:
            sic = deepcopy(el)
            idx = parent.index(el)
            parent.remove(el)
            choice = Element(self.tei_ns + 'choice')
            parent.insert(idx, choice)
            # reinsert beneath sic element
            SubElement(choice, self.tei_ns + 'sic').append(sic)
        for alt in it:
            corr = SubElement(choice, self.tei_ns + 'corr')
            if self.resp:
                corr.set('resp', '#' + self.resp)
            corr.text = alt[0]
            if len(alt) == 2:
                cert = SubElement(corr, self.tei_ns + 'certainty',
                                  degree=u'{0:.2f}'.format(alt[1] / 100.0),
                                  locus='value')
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
        Deletes all grapheme zone nodes from the document. Mainly used when
        combining page segmentation algorithms extracting graphemes and OCR
        engines operating on lexemes. Also resets the current scope to the
        first line (and if applicable its first segment).
        """
        for zone in self.doc.iterfind('.//' + self.tei_ns +
                                      "zone[@type='grapheme']"):
            zone.getparent().remove(zone)
        self.line_scope = self.doc.find('.//' + self.tei_ns + 'line')
        self.word_scope = self.doc.find('.//' + self.tei_ns + "zone[@type='segment']")
        self.grapheme_cnt = -1

    def clear_segments(self):
        """
        Deletes all word zone nodes from the document. Mainly used when
        combining page segmentation algorithms extracting lexemes (and
        graphemes) and OCR engines operating on lines. Also resets the current
        scope to the first line.
        """
        for zone in self.doc.iterfind('.//' + self.tei_ns +
                                      "zone[@type='segment']"):
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
                    confidence = int(o['x_wconf'][0])
                self.add_segment(bbox, confidence=confidence)
                self.add_graphemes(''.join(span.itertext()))
                if span.tail:
                    self.clear_segment()
                    # strip trailing whitespace as some engines add it
                    # arbitrarily or for formatting purposes
                    self.add_graphemes(span.tail.rstrip())

    def write_hocr(self, fp):
        """
        Writes the TEI document as an hOCR file.

        Args:
            fp (file): File descriptor to write to.
        """
        page = etree.Element('html', xmlns="http://www.w3.org/1999/xhtml")
        head = SubElement(page, 'head')
        SubElement(head, 'title').text = self.title
        SubElement(head, 'meta', name="ocr-system",
                   content=self.respstmt.values()[-1][self.tei_ns + 'name'])
        capa = "ocr_page"
        if self.lines is not None:
            capa += ", ocr_line"
        if self.segments is not None:
            capa += ", ocrx_word"
        SubElement(head, 'meta', name='ocr-capabilities', content=capa)
        body = SubElement(page, 'body')
        ocr_page = SubElement(body, 'div', title='')
        ocr_page.set('class', 'ocr_page')
        for line in self.doc.iter(self.tei_ns + 'line'):
            ocr_line = SubElement(ocr_page, 'span')
            ocr_line.set('class', 'ocr_line')
            ocr_line.set('title', 'bbox ' + ' '.join([str(line.get('ulx')),
                                                      str(line.get('uly')),
                                                      str(line.get('lrx')),
                                                      str(line.get('lry'))]))
            # get text not in word segments interleaved with segments
            ocrx_word = None
            for seg in line.xpath('child::node()'):
                if ocrx_word is not None:
                    ocrx_word.text += ' '
                if isinstance(seg, etree._ElementStringResult):
                    if ocr_line.text is None:
                        ocr_line.text = ''
                    ocr_line.text += seg
                else:
                    # zone from
                    ocrx_word = SubElement(ocr_line, 'span')
                    ocrx_word.set('class', 'ocrx_word')
                    title = 'bbox ' + ' '.join([str(seg.get('ulx')),
                                               str(seg.get('uly')),
                                               str(seg.get('lrx')),
                                               str(seg.get('lry'))])
                    cert = seg.find('.//{0}certainty'.format(self.tei_ns))
                    if cert is not None:
                        title += '; x_wconf ' + str(int(100.0 *
                                                    float(cert.get('degree'))))
                    ocrx_word.set('title', title)
                    ocrx_word.text = ''.join(seg.itertext())
            SubElement(ocr_page, 'br')
        fp.write(etree.tostring(page, pretty_print=True,
                 doctype='<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 '
                         'Transitional//EN" '
                         '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
                 xml_declaration=True, encoding='utf-8'))
        fp.flush()

    def write_abbyyxml(self, fp):
        """
        Writes the TEI document in a format reminiscent of Abbyy FineReader's
        XML output. Its basic format is:

        <text>
        <line l="0" r="111" t="6" b="89">
        <charParams l="0" r="78" t="6" b="89" charConfidence="76" wordStart="true">D</charParams>
        <charParams l="86" r="111" t="24" b="89" charConfidence="76" wordStart="false">e</charParams>
        </line>
        ....
        </text>

        Args:
            fp (file): File descriptor to write to.
        """
        page = etree.Element('document')
        p = etree.SubElement(page, 'page')
        surface = self.doc.find('.//{0}sourceDoc/{0}surface'.format(self.tei_ns))
        p.set('width', surface.get('lrx'))
        p.set('height', surface.get('lry'))
        p.set('originalCoords', '1')
        text = etree.SubElement(page, 'text')
        last_seg_id = None
        for line in self.doc.iter(self.tei_ns + 'line'):
            lel = SubElement(text, 'line')
            lel.set('l', line.get('ulx'))
            lel.set('t', line.get('uly'))
            lel.set('r', line.get('lrx'))
            lel.set('b', line.get('lry'))
            for g in line.iter(self.tei_ns + 'g'):
                el = SubElement(lel, 'charParams')
                seg = g.xpath("ancestor::*[@type='segment']")
                if seg and seg[0].get(self.xml_ns  + 'id') != last_seg_id:
                    el.set('wordStart', 'true')
                    last_seg_id = seg[0].get(self.xml_ns + 'id')
                else:
                    el.set('wordStart', 'false')
                el.text = ''.join(g.itertext())
                if g.getparent().getparent().get('type') == 'grapheme':
                    el.set('l', g.getparent().getparent().get('ulx'))
                    el.set('t', g.getparent().getparent().get('uly'))
                    el.set('r', g.getparent().getparent().get('lrx'))
                    el.set('b', g.getparent().getparent().get('lry'))
                cert = self.doc.xpath("//*[local-name()='certainty' and @target=$tag]",
                                      tag='#' + g.get(self.xml_ns + 'id'))
                if len(cert):
                   el.set('charConfidence', str(100.0 * float(cert[0].get('degree'))))
        fp.write(etree.tostring(page, xml_declaration=True, encoding='utf-8'))
        fp.flush()

    def write_text(self, fp):
        """
        Writes the TEI document as plain text.

        Args:
            fp (file): File descriptor to write to.
        """
        for line in self.lines:
            fp.write(line[-1].encode('utf-8').strip())
            fp.write('\n')
        fp.flush()

    def write(self, fp):
        """
        Writes the TEI XML document to a file object.

        Args:
            fp (file): file object to write to
        """
        fp.write(etree.tostring(self.doc, xml_declaration=True, pretty_print=True,
                                encoding='utf-8'))
        fp.flush()

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
        self.seg_cnt = len(list(self.doc.iterfind('.//' + self.tei_ns + "zone[@type='segment']"))) - 1
        self.grapheme_cnt = len(list(self.doc.iter(self.tei_ns + 'g'))) - 1


# populate properties on the class. Note that it operates on the TEIFacsimile
# class itself.
for field in TEIFacsimile.fields:
    setattr(TEIFacsimile, field, property(partial(TEIFacsimile._generic_getter,
            field=field), partial(TEIFacsimile._generic_setter, field=field)))
