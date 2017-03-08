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
from itertools import islice
from copy import deepcopy

from nidaba.nidabaexceptions import NidabaTEIException, NidabaRecordException


class _micro_hocr(object):
    """ 
    A simple class encapsulating hOCR attributes
    """
    def __init__(self):
        self.output = u'' 

    def __str__(self):
        return self.output

    def add(self, *args):
        if self.output:
            self.output += u'; '
        for arg in args:
            if isinstance(arg, str):
                self.output += arg + ' ' 
            elif isinstance(arg, tuple):
                self.output += u','.join([str(v) for v in arg]) + u' '
            else:
                self.output += str(arg) + u' '
        self.output = self.output.strip()


def _delta(root=(0, 0, 0, 0), coordinates=None):
    """Calculates the running delta from a root coordinate according to the
    hOCR standard.

    It uses a root bounding box (x0, y0, x1, y1) and calculates the delta from
    the points (min(x0, x1), min(y0, y1)) and (min(x0, x1), max(y0, y1)) for
    the first and second pair of values in a delta (dx0, dy0, dx1, dy1)
    respectively.

    Args:
        coordinates (list): List of tuples of length 4 containing absolute
                            coordinates for character bounding boxes.

    Returns:
        A tuple dx0, dy0, dx1, dy1
    """
    for box in coordinates:
        yield (min(box[0], box[2]) - min(root[0], root[2]),
               min(box[1], box[3]) - min(root[1], root[3]),
               max(box[0], box[2]) - min(root[0], root[2]),
               max(box[1], box[3]) - max(root[1], root[3]))
        root = box


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


class OCRRecord(object):
    """
    A composite object of containing recognition results for a single scanned
    page.

    A page is divided into lines which may contain segments and graphemes. For
    practical purposes this means that the appropriate line or segment (the
    later overriding the first) has to be brought into scope first before
    adding any characters to it.
    
    Each element may be associated with a responsibility statement, identifying
    the origin of each alteration if the final serialization supports it.
    """

    # automatically generated properties on the class
    fields = ['title', 'author', 'editor', 'funder', 'principal', 'sponsor',
              'meeting', 'edition', 'publisher', 'distributor', 'authority',
              'idno', 'pub_place', 'licence', 'series_title', 'note',
              'source_desc', 'img', 'dimensions']

    xml_ns = '{http://www.w3.org/XML/1998/namespace}'
    tei_ns = '{http://www.tei-c.org/ns/1.0}'
    abbyy_ns = '{http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml}'

    # automatically generated properties in the fileDesc element and xpath to their location
    _tei_fields = [('titleStmt', [('title', '/' + tei_ns + 'title',), 
                                  ('author', '/' + tei_ns + 'author', 'ref'),
                                  ('editor', '/' + tei_ns + 'editor',  'ref'),
                                  ('funder', '/' + tei_ns + 'funder', 'ref'),
                                  ('principal', '/' + tei_ns + 'principal', 'ref'),
                                  ('sponsor', '/' + tei_ns + 'sponsor', 'ref'),
                                  ('meeting', '/' + tei_ns + 'meeting'),
                                  ]),
                   ('editionStmt', [('edition', '/' + tei_ns + 'edition')]),
                   ('publicationStmt', [('publisher', '/' + tei_ns + 'publisher', 'target'),
                                        ('distributor', '/' + tei_ns + 'distributor', 'target'),
                                        ('authority', '/' + tei_ns + 'authority', 'target'),
                                        ('idno', '/' + tei_ns + 'idno', 'type'),
                                        ('pub_place', '/' + tei_ns + 'pubPlace'),
                                        ('licence', '/{0}availability/{0}licence'.format(tei_ns), 'target'),
                                       ]),
                   ('seriesStmt', [('series_title', '/' + tei_ns + 'p')]),
                   ('notesStmt', [('note', '/' + tei_ns + 'note')]),
                   ('sourceDesc', [('source_desc', '/' + tei_ns + 'p')])
                  ] 

    def __init__(self):
        self.meta = {}
        self.img = None
        self.respstmt = OrderedDict()
        self.resp_scope = None
        self.line_scope = None
        self.segment_scope = None

        self.lines = OrderedDict()

    # generic setter/getter for metadata
    def _generic_getter(self, field):
        if field in self.meta:
            return self.meta[field]
        else:
            return None

    def _generic_setter(self, value, field):
        self.meta[field] = value

    # responsibility statement functionality
    def add_respstmt(self, resp, name, **kwargs):
        """
        Adds a responsibility statement and returns its identifier.

        The new responsibility statement is automatically scoped.
        Args:
            resp (unicode): Nature of the responsible process.
            name (unicode): Text describing the processing software.
            kwargs (dict): Additional data used be the final serialization.

        Returns:
            A string containing the respstmt ID.
        """
        kwargs['resp'] = resp
        kwargs['name'] = name
        id = u'resp_' + unicode(len(self.respstmt) + 1)
        self.respstmt[id] = kwargs
        self.resp_scope = id
        return id

    def scope_respstmt(self, id):
        """
        Scopes a responsibility statement.

        Args:
            id (unicode): String of targeted resposibility statement.

        Raises:
            NidabaRecordException if the responsibility statement couldn't be
            found.
        """
        if id not in self.respstmt:
            raise NidabaRecordException('No such responsibility statement')
        self.resp_scope = id

    def reset_respstmt_scope(self):
        """
        Clears the current responsibility scope.
        """
        self.resp_scope = None

    #  writer functions for topographical data
    def add_line(self, dim, **kwargs):
        """
        Marks the start of a new topographical line and scopes it.

        Args:
            dim (tuple): A tuple (x0, y0, x1, y1) denoting the bounding box.
            kwargs (dict): Additional data used by the final serialization.

        Returns:
            A string containing the line's identifier.
        """
        id = u'line_' + unicode(len(self.lines) + 1)
        kwargs['bbox'] = dim
        kwargs['content'] = OrderedDict()
        if self.resp_scope:
            kwargs['resp'] = self.resp_scope
        self.lines[id] = kwargs
        self.line_scope = id
        return id

    def add_segment(self, dim, language=None, confidence=None, **kwargs):
        """
        Marks the beginning of a new topographical segment in the current
        scope. Most often this correspond to a word recognized by an engine.

        Args:
            dim (tuple): A tuple containing the bounding box (x0, y0, x1, y1)
            lang (unicode): Optional identifier of the segment language.
            confidence (int): Optional confidence value between 0 and 100.
            kwargs (dict): Additional data used by the final serialization.

        Returns:
            A string containing the segment's indeitifier.

        Raises:
            NidabaRecordException if no line is scoped.
        """
        if not self.line_scope:
            raise NidabaRecordException('No line scoped.')
        id = u'seg_' + unicode(len(self.segments) + 1)
        kwargs['type'] = 'segment'
        kwargs['bbox'] = dim
        if language:
            kwargs['language'] = language
        if confidence:
            if confidence < 0 or confidence > 100:
                raise NidabaRecordException('Segmentconfidence {} outside valid '
                                            'range'.format(confidence))
            kwargs['confidence'] = confidence
        if self.resp_scope:
            kwargs['resp'] = self.resp_scope

        kwargs['content'] = OrderedDict()
        self.lines[self.line_scope]['content'][id] = kwargs
        self.segment_scope = id
        return id

    # actual recognition result writer
    def add_graphemes(self, it):
        """
        Adds a number of graphemes to the current scope (either line or segment).

        A line and/or segment has to be created beforehand.

        Args:
            it (iterable): An iterable returning a dictionary which at least
                           contains a key 'grapheme' with the recognition
                           result. A bounding box has to be placed under the
                           key 'bbox'; a confidence value in the range 0-100
                           (int) is expected under 'confidence'. Additional
                           data (style etc.) will be retained for serializer
                           use.
        """
        if self.line_scope is None:
            raise NidabaRecordException('No element scoped.')
        if self.segment_scope is not None:
            target = self.lines[self.line_scope]['content'][self.segment_scope]['content']
        else:
            target = self.lines[self.line_scope]['content']
        gr_cnt = len(self.graphemes)
        ids = []
        for glyph in it:
            gr_cnt += 1
            id = u'grapheme_' + unicode(gr_cnt)
            ids.append(id)
            glyph['type'] = 'grapheme'
            if 'confidence' in glyph and (glyph['confidence'] < 0 or \
                                          glyph['confidence'] > 100 ):
                raise NidabaRecordException('Glyph confidence {} outside valid '
                                            'range'.format(glyph['confidence']))
            if 'grapheme' not in glyph:
                raise NidabaRecordException('Mandatory field missing when adding graphemes.')
            if self.resp_scope:
                glyph['resp'] = self.resp_scope
            target[id] = glyph
        return ids

    
    def add_choices(self, id, it):
        """
        Adds alternative interpretations to an element.

        Args:
            id (unicode): ID of the element.
            it (iterable): An iterable returning a dictionary containing an
            alternative reading ('alternative') and an optional confidence
            value ('confidence') in the range between 0 and 100.

        Raises:
            NidabaRecordException if no element with the ID could be found.
        """
        if id in self.lines:
            target = self.lines[id]
        for line in self.lines.itervalues():
            if id in line['content']:
                target = line['content'][id]
                break
            for seg in line['content'].itervalues():
                if 'content' in seg and id in seg['content']:
                    target = seg['content'][id]
                    break
        alt = {'content': list(it)}
        if self.resp_scope:
            alt['resp'] = self.resp_scope
        target['alternatives'] = alt

    # scoping of topographical elements
    def scope_line(self, id):
        """
        Scopes a line.

        Args:
            id (unicode): ID of the line to scope.

        Raises:
            NidabaRecordException if no line with the ID could be found.
        """
        if id not in self.lines:
            raise NidabaRecordException('Invalid line ID.')
        self.line_scope = id

    def scope_segment(self, id):
        """
        Scopes a segment (and by association its line).

        Args:
            id (unicode): ID of the segment to scope.

        Raises
        """
        for line_id, line in self.lines.iteritems():
            if id in line['content']:
                self.line_scope = line_id
                self.segment_scope = id
                return
        raise NidabaRecordException('Invalid segment ID.')

    def reset_line_scope(self):
        """
        Resets line scope.
        """
        self.line_scope = None
        self.segment_scope = None

    def reset_segment_scope(self):
        """
        Resets segment scope.
        """
        self.segment_scope = None

    # clearing topographical data
    def clear_lines(self):
        """
        Deletes all lines and their content from the record.
        """
        self.reset_line_scope()
        self.lines = OrderedDict()

    def clear_segments(self):
        """
        Deletes all segments and their content from the record.
        """
        self.reset_segment_scope()
        self.segment_scope = None
        for line in self.lines.itervalues():
            line['content'] = OrderedDict()

    def clear_graphemes(self):
        """
        Deletes all graphemes from the record.
        """
        for line in self.lines.itervalues():
            for seg in line['content'].itervalues():
                if seg['type'] == 'grapheme':
                    line['content'] = OrderedDict()
                    break
                else:
                    seg['content'] = OrderedDict()

    # properties offering short cuts (line are already top-level records)
    @property
    def segments(self):
        """
        Returns an OrderedDict of segments with each segment being a dictionary.
        """
        seg = OrderedDict()
        for line in self.lines.itervalues():
            for seg_id, el in line['content'].iteritems():
                if el['type'] == 'segment':
                    seg[seg_id] = el
        return seg

    @property
    def graphemes(self):
        """
        Returns a list of graphemes with each grapheme being a dictionary.
        """
        g = OrderedDict()
        for line_id, line in self.lines.iteritems():
            for seg_id, el in line['content'].iteritems():
                if el['type'] == 'segment':
                    for g_id, gr in el['content'].iteritems():
                        g[g_id] = gr
                elif el['type'] == 'grapheme':
                    g[seg_id] = el
        return g

    # de-/serializers
    def load_tei(self, fp):
        """
        Reads in a TEI facsimile and populates the record.

        Args:
            fp (File): Source file descriptor.
        """

        doc = etree.parse(fp)

        self.respstmt = OrderedDict()
        self.resp_scope = None

        for stmt, fields in self._tei_fields:
            stmt_el = doc.find('{0}teiHeader/{0}fileDesc/{0}{1}'.format(self.tei_ns, stmt))
            if stmt_el is None:
                continue
            for field in fields:
                f_el = stmt_el.find('./' + field[1])
                if f_el is not None:
                    if len(field) == 3 and f_el.get(field[2]):
                        self.meta[field[0]] = [f_el.text, f_el.get(field[2])]
                    else:
                        self.meta[field[0]] = f_el.text

        for resp in doc.iter(self.tei_ns + 'respStmt'):
            id = resp.get(self.xml_ns + 'id')
            r = resp.find('.//{}resp'.format(self.tei_ns)).text
            n = resp.find('.//{}name'.format(self.tei_ns)).text
            self.respstmt[id] = {'resp': r, 'name': n}

        surface = doc.find('{0}sourceDoc/{0}surface'.format(self.tei_ns))
        if surface.get('lrx') is not None and surface.get('lry') is not None:
            self.dimensions = (int(surface.get('lrx')), int(surface.get('lry')))
        graphic = surface.find('{}graphic'.format(self.tei_ns))
        if graphic is not None:
            self.img = graphic.get('url')

        root_zone = doc.find('{0}sourceDoc/{0}surface/{0}zone'.format(self.tei_ns))

        corr_flag = False
        alts = []
        sic = None
        last_el = None

        def _get_dict_from_key(id):
            if id in self.lines:
                return self.lines[id]
            for line in self.lines.itervalues():
                if id in line['content']:
                    return line['content'][id]
                for seg in line['content'].itervalues():
                    if 'content' in seg and id in seg['content']:
                        return seg['content'][id]

        for el in islice(root_zone.iter(), 1, None):
            if el.tag != self.tei_ns + 'corr' and corr_flag:
                corr_flag = False
                #flush alternatives
                self.add_choices(sic, alts)
                alts = []
            elif el.tag == self.tei_ns + 'sic':
                sic = None
            elif el.tag == self.tei_ns + 'corr':
                corr_flag = True
                alts.append({'alternative': ''.join(el.text)})
                last_el = alts[-1]
            elif el.tag == self.tei_ns + 'line':
                if el.get('resp') is not None:
                    self.scope_respstmt(el.get('resp')[1:])
                id = self.add_line((int(el.get('ulx')), int(el.get('uly')),
                                    int(el.get('lrx')), int(el.get('lry'))))
                last_el = _get_dict_from_key(id)
                sic = id if not sic else None
            elif el.tag == self.tei_ns + 'zone' and el.get('type') == 'segment':
                if el.get('resp') is not None:
                    self.scope_respstmt(el.get('resp')[1:])
                id = self.add_segment((int(el.get('ulx')), int(el.get('uly')),
                                       int(el.get('lrx')), int(el.get('lry'))))
                last_el = _get_dict_from_key(id)
                sic = id if not sic else None
            elif el.tag == self.tei_ns + 'zone' and el.get('type') == 'grapheme':
                gr = {'bbox': (int(el.get('ulx')), int(el.get('uly')),
                               int(el.get('lrx')), int(el.get('lry'))), 
                           'grapheme': el.findtext('./{0}seg/{0}g'.format(self.tei_ns))
                          }
                id = self.add_graphemes([gr])[0]
                last_el = _get_dict_from_key(id)
                sic = id if not sic else None
            elif el.tag == self.tei_ns + 'certainty':
                last_el['confidence'] = float(el.get('degree')) * 100
            elif el.tag in [self.tei_ns + 'seg', self.tei_ns + 'g', self.tei_ns + 'choice']:
                pass
            else:
                raise NidabaRecordException('Unknown tag {} encountered'.format(el.tag))

    def write_tei(self, fp):
        """
        Serializes the record to a TEI facsimile.

        Args:
            fp (File): Target file descriptor.
        """
        doc = Element('TEI', nsmap={None: 'http://www.tei-c.org/ns/1.0'},
                      version='5.0')
        header = SubElement(doc, self.tei_ns + 'teiHeader')
        fileDesc = SubElement(header, self.tei_ns + 'fileDesc')

        sourceDoc = SubElement(doc, self.tei_ns + 'sourceDoc')
        kwargs = {}
        if self.dimensions:
            kwargs = {'ulx': '0', 'uly': '0', 
                      'lrx': str(self.dimensions[0]),
                      'lry': str(self.dimensions[1])
                     }
        surface = SubElement(sourceDoc, self.tei_ns + 'surface', **kwargs)
        if self.img:
            SubElement(surface, self.tei_ns + 'graphic', url=self.img)

        surface_zone = SubElement(surface, self.tei_ns + 'zone')

        for stmt, fields in self._tei_fields:
            # create *Stmt in correct order
            parent = Element(self.tei_ns + stmt)
            for field in fields:
                if field[0] in self.meta:
                    el = parent
                    for node in field[1].split('/{')[1:]:
                        el = SubElement(el, '{' + node)
                    value = self.meta[field[0]]
                    if isinstance(value, list):
                        el.set(field[2], value[1])
                        value = value[0]
                    el.text = value
            # insert *Stmt only when needed
            if list(parent):
                fileDesc.append(parent)

        titleStmt = doc.find('{0}teiHeader/{0}fileDesc/{0}titleStmt'.format(self.tei_ns))

        if titleStmt is None:
            titleStmt = Element(self.tei_ns + 'titleStmt')
            fileDesc.insert(0, titleStmt)

        for id, resp in self.respstmt.iteritems():
            r = SubElement(titleStmt, self.tei_ns + 'respStmt')
            r.set(self.xml_ns + 'id', id)
            SubElement(r, self.tei_ns + 'resp').text = resp['resp']
            SubElement(r, self.tei_ns + 'name').text = resp['name']

        def _set_confidence(el, up, dic):
            cert = None
            if 'confidence' in dic:
                cert = SubElement(el, self.tei_ns + 'certainty',
                                  degree=u'{0:.2f}'.format(dic['confidence'] / 100.0), 
                                  locus='value')
                if el.get(self.xml_ns + 'id'):
                    cert.set('target', '#' + el.get(self.xml_ns + 'id'))
            if 'resp' in up:
                el.set('resp', '#' + up['resp'])
                if cert is not None:
                    cert.set('resp', '#' + up['resp'])

        def _wrap_choices(alternatives, sic, parent):
            choice = SubElement(parent, self.tei_ns + 'choice')
            sic_el = SubElement(choice, self.tei_ns + 'sic')
            sic_el.append(sic)
            for alt in alternatives['content']:
                corr = SubElement(choice, self.tei_ns + 'corr')
                corr.text = alt['alternative']
                _set_confidence(corr, alternatives, alt)

        def _add_grapheme(grapheme_id, grapheme, parent):
            g_el = Element(self.tei_ns + 'zone',
                           type='grapheme')
            g_el.set(self.xml_ns + 'id', grapheme_id)
            if 'bbox' in grapheme:
                g_el.set('ulx', str(grapheme['bbox'][0]))
                g_el.set('uly', str(grapheme['bbox'][1]))
                g_el.set('lrx', str(grapheme['bbox'][2]))
                g_el.set('lry', str(grapheme['bbox'][3]))

            if 'alternatives' in grapheme:
                _wrap_choices(grapheme['alternatives'], g_el, parent)
            else:
                parent.append(g_el)
            glyph = SubElement(SubElement(g_el, self.tei_ns + 'seg'), self.tei_ns + 'g')
            glyph.text = grapheme['grapheme']
            _set_confidence(g_el, grapheme, grapheme)

        for line_id, line in self.lines.iteritems():
            line_el = Element(self.tei_ns + 'line', ulx=str(line['bbox'][0]),
                              uly=str(line['bbox'][1]),
                              lrx=str(line['bbox'][2]),
                              lry=str(line['bbox'][3])) 
            line_el.set(self.xml_ns + 'id', line_id)
            _set_confidence(line_el, line, line)
            if 'alternatives' in line:
                _wrap_choices(line['alternatives'], line_el, surface_zone)
            else:
                surface_zone.append(line_el)
            for seg_id, seg in line['content'].iteritems():
                if seg['type'] == 'segment':
                    seg_el = Element(self.tei_ns + 'zone',
                                     ulx=str(seg['bbox'][0]),
                                     uly=str(seg['bbox'][1]),
                                     lrx=str(seg['bbox'][2]),
                                     lry=str(seg['bbox'][3]),
                                     type=seg['type'])
                    seg_el.set(self.xml_ns + 'id', seg_id)
                    _set_confidence(seg_el, seg, seg)
                    for grapheme_id, grapheme in seg['content'].iteritems():
                        _add_grapheme(grapheme_id, grapheme, seg_el)
                    if 'alternatives' in seg:
                        _wrap_choices(seg['alternatives'], seg_el, line_el)
                    else:
                        line_el.append(seg_el)
                elif seg['type'] == 'grapheme':
                    _add_grapheme(seg_id, seg, line_el)
                else:
                    raise NidabaRecordException('Unknown nodes beneath line records')
        fp.write(etree.tostring(doc, xml_declaration=True, encoding='utf-8', pretty_print=True))
        fp.flush()

    def write_abbyyxml(self, fp):
        """
        Writes the TEI document in a format reminiscent of Abbyy FineReader's
        XML output. Its basic format is:

        <document>
        <page>
        <text>
        <line l="0" r="111" t="6" b="89">
        <charParams l="0" r="78" t="6" b="89" charConfidence="76" wordStart="true">D</charParams>
        <charParams l="86" r="111" t="24" b="89" charConfidence="76" wordStart="false">e</charParams>
        </line>
        ....
        </text>
        </page>
        </document>

        Please note that alternative readings as produced for example by spell
        checking are dropped from the output. Responsibility statements,
        metadata, and source image information is likewise lost.

        Args:
            fp (file): File descriptor to write to.
        """
        page = Element('document',
                       xmlns='http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml',
                       version='1.0',
                       producer='nidaba')
        p = SubElement(page, 'page')
        p.set('width', str(self.dimensions[0]))
        p.set('height', str(self.dimensions[1]))
        p.set('resolution', '0')
        p.set('originalCoords', '1')
        b = SubElement(p, 'block', blockType='Text')
        text = SubElement(b, 'text')
        par = SubElement(text, 'par')
        for line in self.lines.itervalues():
            lel = SubElement(par, 'line')
            # XXX: meaning of baseline is nowere documented
            lel.set('baseline', '0')
            lel.set('l', str(line['bbox'][0]))
            lel.set('t', str(line['bbox'][1]))
            lel.set('r', str(line['bbox'][2]))
            lel.set('b', str(line['bbox'][3]))
            for seg in line['content'].itervalues():
                if seg['type'] == 'segment':
                    formatting = SubElement(lel, 'formatting')
                    if 'language' in seg:
                        formatting.set('lang', seg['language'])
                    word_start = True
                    for g in seg['content'].itervalues():
                        if 'bbox' not in g:
                            raise NidabaRecordException('No bounding box for grapheme')
                        el = SubElement(formatting, 'charParams')
                        if word_start:
                            el.set('wordStart', 'true')
                            word_start = False
                        else:
                            el.set('wordStart', 'false')
                        el.text = g['grapheme']
                        el.set('l', str(g['bbox'][0]))
                        el.set('t', str(g['bbox'][1]))
                        el.set('r', str(g['bbox'][2]))
                        el.set('b', str(g['bbox'][3]))
                        if 'confidence' in g:
                           el.set('charConfidence', str(g['confidence']))
                elif seg['type'] == 'grapheme':
                    formatting = SubElement(lel, 'formatting')
                    if 'language' in seg:
                        formatting.set('lang', seg['language'])
                    el = SubElement(formatting, 'charParams')
                    el.text = g['grapheme']
                    el.set('l', str(g['bbox'][0]))
                    el.set('t', str(g['bbox'][1]))
                    el.set('r', str(g['bbox'][2]))
                    el.set('b', str(g['bbox'][3]))
                    if 'confidence' in g:
                       el.set('charConfidence', str(g['confidence']))
                else:
                    raise NidabaRecordException('Unknown nodes beneath line records')
        fp.write(etree.tostring(page, xml_declaration=True, encoding='utf-8'))
        fp.flush()

    def write_alto(self, fp):
        """
        Serializes the record as an ALTO XML document.

        See [0] for further information and schemata. Output will conform to
        version 3.1.

        Please note that the output will not be split into a series of
        "paragraphs" as segmentation algorithms don't produce them and they are
        dependent on typographic convention. Scores for alternatives are
        dropped as the standard does not provide for a way to encode them.
        Character confidences are rounded to the next lower confidence value
        (.98 -> 0, 0.05 -> 9).

        Alternatives are only serialized for segments. Line and grapheme
        alternatives are discarded.

        Args:
            fp (file): File descriptor to write to.

        [0] http://www.loc.gov/standards/alto/
        """
        alto = etree.Element('alto', xmlns="http://www.loc.gov/standards/alto/ns-v3#")
        description = SubElement(alto, 'Description')
        SubElement(description, 'MeasurementUnit').text = 'pixel'

        # use the image url as source image file name
        source_img = SubElement(description, 'sourceImageInformation')
        if self.img is not None:
            SubElement(source_img, 'fileName').text = self.img
        # convert responsibility statements to ocrProcessingSteps. As TEI
        # offers no way to distinguish between pre-, OCR, and postprocessing
        # for responsibility statements everything before a respStmt containing
        # 'recognition' is converted into preprocessing and everything after it
        # to postprocessing.
        ocr_proc = SubElement(description, 'OCRProcessing')
        ocr_proc.set('ID', 'OCR_0')
        mode = 'preProcessingStep'
        for id, respstmt in self.respstmt.iteritems():
            if 'recognition' in respstmt['resp'] and mode == 'preProcessingStep':
                mode = 'ocrProcessingStep'
            proc = SubElement(ocr_proc, mode)
            SubElement(proc, 'processingStepDescription').text = respstmt['resp']
            ps = SubElement(proc, 'processingSoftware')
            SubElement(ps, 'softwareName').text = respstmt['name']
            if mode == 'ocrProcessingStep':
                mode = 'postProcessingStep'

        layout = SubElement(alto, 'Layout')
        page = SubElement(layout, 'Page')
        if self.dimensions is not None:
            page.set('WIDTH', str(self.dimensions[0]))
            page.set('HEIGHT', str(self.dimensions[1]))
        page.set('PHYSICAL_IMG_NR', '0')
        page.set('ID', 'page_0')

        # why do all OCR formats insist on creating 'paragraph' containers? As
        # paragraphs are highly variable and dependent on typographic
        # conventions all text on the page is wrapped into a single paragraph.
        print_space = SubElement(page, 'PrintSpace')
        print_space.set('HPOS', str(0.0))
        print_space.set('VPOS', str(0.0))
        if self.dimensions is not None:
            print_space.set('WIDTH', str(self.dimensions[0]))
            print_space.set('HEIGHT', str(self.dimensions[1]))
        text_block = SubElement(print_space, 'TextBlock')
        text_block.set('HPOS', str(0.0))
        text_block.set('VPOS', str(0.0))
        text_block.set('ID', 'textblock_0')
        if self.dimensions is not None:
            text_block.set('WIDTH', str(self.dimensions[0]))
            text_block.set('HEIGHT', str(self.dimensions[1]))
      
        for line_id, line in self.lines.iteritems():
            text_line = SubElement(text_block, 'TextLine')
            text_line.set('HPOS', str(line['bbox'][0]))
            text_line.set('VPOS', str(line['bbox'][1]))
            text_line.set('WIDTH', str(line['bbox'][2] - line['bbox'][0]))
            text_line.set('HEIGHT', str(line['bbox'][3] - line['bbox'][1]))
            text_line.set('ID', line_id)

            # There are 3 cases of content beneath a line: a list of graphemes
            # (which are outright dumped into a SINGLE String element), some
            # segments (each is converted to a String or SP node depending on
            # content), or some corr node which are converted to String nodes
            # containing ALTERNATIVE nodes.
            for seg_id, seg in line['content'].iteritems():
                if seg['type'] == 'grapheme':
                    text = u''
                    certs = []
                    for g in line['content'].itervalues():
                        text += g['grapheme']
                        # confidences for graphemes are integers between 0 and
                        # 9 with 0 (wtf?) representing highest confidence
                        if 'confidence' in g:
                            certs.append(str(int(10 - 10 * (g['confidence']/100.0))))
                    text_el = SubElement(text_line, 'String')
                    text_el.set('CONTENT', text)
                    text_el.set('CC', ' '.join(certs))
                    break
                elif seg['type'] == 'segment':
                    text = ''.join(x['grapheme'] for x in seg['content'].itervalues())
                    if text.isspace():
                        text_el = SubElement(text_line, 'SP')
                    else:
                        text_el = SubElement(text_line, 'String')
                        text_el.set('CONTENT', text)
                        # extract word confidences
                        if 'confidence' in seg:
                            text_el.set('WC', str(seg['confidence'] / 100.0))
                        certs = []
                        # extract character confidences
                        for g in seg['content'].itervalues():
                            if 'confidence' in g:
                                certs.append(str(int(10 - 10 * (g['confidence']/100.0))))
                        if certs:
                            text_el.set('CC', ' '.join(certs))

                    text_el.set('HPOS', str(seg['bbox'][0]))
                    text_el.set('VPOS', str(seg['bbox'][1]))
                    text_el.set('WIDTH', str(seg['bbox'][2] - seg['bbox'][0]))
                    text_el.set('HEIGHT', str(seg['bbox'][1] - seg['bbox'][3]))
                    text_el.set('ID', seg_id)
                    if 'alternatives' in seg:
                        for corr in seg['alternatives']['content']:
                            SubElement(text_el, 'ALTERNATIVE').text = corr['alternative']
            # add an empty String element if no children exist
            if not list(text_line):
                text_el = SubElement(text_line, 'String')
                text_el.set('CONTENT', '')
        fp.write(etree.tostring(alto, pretty_print=True,
                 xml_declaration=True, encoding='utf-8'))
        fp.flush()

    def load_hocr(self, fp):
        """
        Reads an hOCR file and populates the record.

        Args:
            fp (file): File descriptor to read from.
        """
        doc = etree.HTML(fp.read())
        el = doc.find(".//meta[@name='ocr-system']")
        if el is not None:
            self.add_respstmt(el.get('content'), 'ocr-system')
        page = doc.find('body/div[@class="ocr_page"]')
        o = _parse_hocr(page.get('title'))
        if 'bbox' in o:
            self.dimensions = o['bbox'][2:]
        if 'image' in o:
            self.img = o['image'][0]

        corr_flag = False
        sic = None
        alts = []
        cuts = []
        for el in page.iter('span', 'ins', 'del'):
            el_class = el.get('class')
            if el_class != 'alt' and corr_flag:
                corr_flag = False
                #flush alternatives
                self.add_choices(sic, alts)
                alts = []
            if el.tag == 'ins':
                sic = None
            elif el.tag == 'del':
                corr_flag = True
                o = _parse_hocr(el.get('title'))
                alts.append({'confidence': 100 - o['x_cost'][0],
                             'alternative': ''.join(el.itertext())})
            elif el_class == 'ocr_line':
                o = _parse_hocr(el.get('title'))
                id = self.add_line(o['bbox'])
                if el.xpath('.//span[starts-with(@class, "ocrx")]') is None:
                    sym = ''.join(el.itertext())
                    self.add_graphemes([{'grapheme': x} for x in sym])
                sic = id if not sic else None
            elif 'ocrx' in el_class:
                o = _parse_hocr(el.get('title'))
                id = self.add_segment(o['bbox'], o['x_conf'] if 'x_conf' in o else None)
                sic = id if not sic else None
                sym = ''.join(el.itertext())
                self.add_graphemes([{'grapheme': x} for x in sym])

    def write_hocr(self, fp):
        """
        Serializes the OCR record in hOCR format.

        Metadata except image source and dimensions are lost, as are
        responsibility statements. Alternatives EXCEPT grapheme alternatives
        are inserted using the INS-DEL syntax described in section 10 of the
        hOCR standard [0]. Grapheme coordinates and confidences are added as
        cuts/x_confs to the ocr_line element.

        [0] https://docs.google.com/document/d/1QQnIQtvdAC_8n92-LhwPcjtAUFwBlzE8EWnKAxlgVf0/preview

        Args:
            fp (file): File descriptor to write to.
        """
        page = etree.Element('html', xmlns="http://www.w3.org/1999/xhtml")
        head = SubElement(page, 'head')
        if 'title' in self.meta:
            SubElement(head, 'title').text = self.meta['title']
        if self.respstmt:
            SubElement(head, 'meta', name="ocr-system",
                       content=self.respstmt.values()[-1]['name'])
        capa = "ocr_page"
        if self.lines:
            capa += ", ocr_line"
        if self.segments:
            capa += ", ocrx_word"
        SubElement(head, 'meta', name='ocr-capabilities', content=capa)

        body = SubElement(page, 'body')
	p_hocr = _micro_hocr()
        if 'dimensions' in self.meta:
		p_hocr.add('bbox', 0, 0, *self.meta['dimensions'])
	if self.img is not None:
		p_hocr.add('image', self.img)
        ocr_page = SubElement(body, 'div', title=str(p_hocr))
        ocr_page.set('class', 'ocr_page')

        def _wrap_alternatives(alternatives, ins, parent):
            span = SubElement(parent, 'span')
            span.set('class', 'alternatives')
            ins_el = SubElement(span, 'ins')
            ins_el.set('class', 'alt')
            ins_el.append(ins)
            for alt in alternatives['content']:
                corr = SubElement(span, 'del')
                corr.set('class', 'alt')
                corr.text = alt['alternative']
                if 'confidence' in alt:
                    corr.set('title', 'x_cost {}'.format(100 - alt['confidence']))

        for line_id, line in self.lines.iteritems():
            ocr_line = Element('span', id=line_id)
            ocr_line.set('class', 'ocr_line')
            ocr_line.text = u''
            l_hocr = _micro_hocr()
            l_hocr.add('bbox', line['bbox'])
            gr_boxes = []
            gr_confidences = []
            if 'alternatives' in line:
                _wrap_alternatives(line['alternatives'], ocr_line, ocr_page)
            else:
                ocr_page.append(ocr_line)
            SubElement(ocr_page, 'br')

            for seg_id, seg in line['content'].iteritems():
                if seg['type'] == 'grapheme':
                    if 'bbox' in seg:
                        gr_boxes.append(seg['bbox'])
                    if 'confidence' in seg:
                        gr_confidences.append(seg['confidence'])
                    ocr_line.text += seg['grapheme']
                elif seg['type'] == 'segment':
                    ocrx_word = Element('span', id=seg_id)
                    ocrx_word.set('class', 'ocrx_word')
                    s_hocr = _micro_hocr()
                    if 'bbox' in seg:
                        s_hocr.add('bbox', seg['bbox'])
                    if 'confidence' in seg:
                        s_hocr.add('x_wconf', seg['confidence'])
                    ocrx_word.set('title', str(s_hocr))
                    ocrx_word.text = u''
                    if 'alternatives' in seg:
                        _wrap_alternatives(seg['alternatives'], ocrx_word, ocr_line)
                    else:
                        ocr_line.append(ocrx_word)
                    for g in seg['content'].itervalues():
                        if 'bbox' in g:
                            gr_boxes.append(g['bbox'])
                        if 'confidence' in g:
                            gr_confidences.append(g['confidence'])
                        ocrx_word.text += g['grapheme']
                else:
                    raise NidabaRecordException('Unknown nodes beneath line records')
            if gr_boxes:
                l_hocr.add('cuts', *list(_delta(line['bbox'], gr_boxes)))
            if gr_confidences:
                l_hocr.add('x_confs', *gr_confidences)
            ocr_line.set('title', str(l_hocr))
        fp.write(etree.tostring(page, pretty_print=True,
                 xml_declaration=True, encoding='utf-8'))
        fp.flush()

    def write_text(self, fp, header=True):
        """
        Writes the OCR record as plain text.

        Args:
            fp (file): File descriptor to write to.
            header (bool): Serialize metadata before the recognized text
                           between '+++'.
        """
        if self.meta and header == True:
            fp.write('+++\n')
            for key, val in self.meta.iteritems():
                fp.write(u'{} = {}\n'.format(key, val).encode('utf-8'))
            fp.write('+++\n')

        for line in self.lines.itervalues():
            fp.write('\n')
            for seg in line['content'].itervalues():
                if seg['type'] == 'grapheme':
                    fp.write(g['grapheme'].encode('utf-8'))
                else:
                    for g in seg['content'].itervalues():
                        fp.write(g['grapheme'].encode('utf-8'))
        fp.flush()


# populate properties on the class. Note that it operates on the TEIFacsimile
# class itself.
for field in OCRRecord.fields:
    setattr(OCRRecord, field, property(partial(OCRRecord._generic_getter,
            field=field), partial(OCRRecord._generic_setter, field=field)))
