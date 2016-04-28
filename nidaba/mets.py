# -*- coding: utf-8 -*-
"""
nidaba.mets
~~~~~~~~~~~

A module for creating METS files from batches.
"""

from __future__ import absolute_import, division, print_function

from lxml import etree
from lxml.etree import Element, SubElement

from collections import OrderedDict
from functools import partial
from itertools import islice
from copy import deepcopy
from datetime import datetime

from nidaba.nidabaexceptions import NidabaTEIException, NidabaRecordException

class METSRecord(object):
    """
    A simple object for creating METS records from (executed) batch definitions.
    """

    xml_ns = '{http://www.w3.org/XML/1998/namespace}'
    mets_ns = '{http://www.loc.gov/METS/}'
    mods_ns = '{http://www.loc.gov/mods/v3}'
    xlink_ns = '{http://www.w3.org/1999/xlink}'

    def __init__(self):
        self.doc = Element('mets', nsmap={None: self.mets_ns[1:-1], 'xlink': self.xlink_ns[1:-1]})
        self.metsHdr = SubElement(self.doc, 'metsHdr', CREATEDATE=datetime.now().isoformat())
        self.dmdSec = SubElement(self.doc, 'dmdSec')
        self.amdSec = SubElement(self.doc, 'amdSec')
        fileSec = SubElement(self.doc, 'fileSec')
        self.fileGrp = SubElement(fileSec, 'fileGrp')

        self.file_id = 0
        self.page_id = 0
        self.structMap = SubElement(self.doc, 'structMap', LABEL="execution_flow")

    def set_descriptive_metadata(self, el, mdtype='MODS'):
        """
        Adds <mdWrap>ed XML metadata to the record.
        """
        self.dmdSec.clear()
        mdwrap = SubElement(self.dmdSec, 'mdWrap', MDTYPE=mdtype)
        mdwrap.append(el)
        self.dmdSec.set('ID', 'dm_0')

    def add_file(self, location, loctype='HANDLE'):
        """
        Adds a file to the fileSec.
        """
        fid = 'file_{}'.format(self.file_id)
        file_el = Element('file', ID=fid)
        self.file_id += 1
        flocat = SubElement(file_el, 'FLocat', LOCTYPE=loctype)
        flocat.set('{}href'.format(self.xlink_ns), location)
        self.fileGrp.append(flocat)
        return fid

    def add_page(self):
        """
        Adds a page to the structMap
        """
        pid = 'page_{}'.format(self.page_id)
        page = Element('div', TYPE='page', ORDER=str(self.page_id), ID=pid)
        self.structMap.append(page)
        self.page_id += 1
        return pid

    def add_div(self, page_id, fid, type='task_output'):
        """
        Adds a div to a page in the structmap.
        """
        el = self.structMap.find('{}div[@ID={}]'.format(self.mets_ns, page_id))
        page = SubElement(el, 'div', TYPE=type, ORDER=str(self.page_id), ID='page_{}'.format(self.page_id))
        SubElement(page, 'fptr', FILEID=fid)

    def write(self, fp):
        """
        Serialize METS document to file pointer.
        """
        fp.write(etree.tostring(doc, xml_declaration, encoding='utf-8', pretty_print=True))
        fp.flush()
