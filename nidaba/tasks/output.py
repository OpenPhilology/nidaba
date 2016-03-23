# -*- coding: utf-8 -*-
"""
nidaba.tasks.output
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Various tasks implementing common housekeeping processes like format
conversion, metadata enrichment, ...

"""

from __future__ import unicode_literals, print_function, absolute_import

import yaml

from nidaba import storage
from nidaba.celery import app
from nidaba.tei import OCRRecord
from nidaba.nidabaexceptions import NidabaTEIException
from nidaba.tasks.helper import NidabaTask

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@app.task(base=NidabaTask, name=u'nidaba.output.metadata',
          arg_values={'metadata': 'file', 'validate': [True, False]})
def tei_metadata(doc, method=u'metadata', metadata=None, validate=False):
    """
    Enriches a TEI-XML document with various metadata from an user-supplied
    YAML file.

    The following fields may be contained in the metadata file with the bolded
    subset mandatory for a valid TEI-XML file. They are grouped by their place
    in the header. Unknown fields are ignored and input is escaped as to
    disable injection.

    Some element may also be extended by increasing their arity, the second
    value is then usually used as a global identifer/locator, i.e. an URL or
    authority control ID.

    titleStmt:

        * ``title``: Title of the resource
        * author: Name of the author of the resource (may be extended)
        * editor: Name of the editor, compiler, translator, etc. of the
                  resource (may be extended)
        * funder: Institution responsible for the funding of the text (may be
                  extended)
        * principal: PI responsible for the creation of the text (may be
                     extended)
        * sponsor: Name of the sponsoring institution (may be extended)
        * meeting: Conference/meeting resulting in the text (may be extended)

    editionStmt:

        * edition: Peculiarities to the underlying edition of the text

    publicationStmt:

        * ``licence``: Licence of the content (may be extended)
        * ``publisher``: Person or agency responsible for the publication of
                     the text (may be extended)
        * distributor: Person or agency responsible for the text's
                       distribution (may be extended)
        * authority: Authority responsible for making the work available
        * idno: Identifier of the publication (may be extended with the type of
                identifier)
        * pub_place: Place of publication
        * date: Date of publication

    seriesStmt:

        * series_title: Title of the series to which the publication belongs

    notesStmt:

        * note: Misc. notes about the text

    sourceDesc:

        * ``source_desc``: Description of the source document

    other:

        * lang: Abbreviation of the language used in the header

    There is a sample file from the OpenPhilology project in the example
    directory.

    Args:
        doc (unicode, unicode): Storage tuple of the input document
        method (unicode):
        metadata (unicode, unicode): Storage tuple of the metadata YAML file

    Returns:
        (unicode, unicode): Storage tuple of the output document

    Raises:
        NidabaTEIException if the resulting document is not TEI compatible and
        validation is enabled.
    """
    with storage.StorageFile(*doc) as fp:
        tei = OCRRecord()
        logger.debug('Reading TEI ({}/{})'.format(*doc))
        tei.load_tei(fp)
    logger.debug('Reading metadata file ({}/{})'.format(*metadata))
    with storage.StorageFile(*metadata) as fp:
        meta = yaml.safe_load(fp)
    for field in tei.fields:
        if field in meta:
            logger.debug('Adding field {} ({})'.format(field, meta[field]))
            setattr(tei, field, meta[field])
    if validate:
        raise NidabaTEIException('Validation not yet implemented.')
    output_path = storage.insert_suffix(doc[1], method, metadata[1])
    with storage.StorageFile(doc[0], output_path, 'wb') as fp:
        logger.debug('Writing TEI to {}'.format(fp.abs_path))
        tei.write_tei(fp)
    return (doc[0], output_path)


@app.task(base=NidabaTask, name=u'nidaba.output.tei2alto')
def tei2alto(doc, method=u'alto'):
    """
    Convert a TEI Facsimile to ALTO XML.

    Args:
        doc (unicode, unicode): Storage tuple of the input document

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    with storage.StorageFile(*doc) as fp:
        tei = OCRRecord()
        logger.debug('Reading TEI ({}/{})'.format(*doc))
        tei.load_tei(fp)
    output_path = storage.insert_suffix(doc[1], method)
    with storage.StorageFile(doc[0], output_path, 'wb') as fp:
        logger.debug('Writing alto to {}'.format(fp.abs_path))
        tei.write_alto(fp)
    return (doc[0], output_path)


@app.task(base=NidabaTask, name=u'nidaba.output.tei2abbyyxml')
def tei2abbyyxml(doc, method=u'abbyyxml'):
    """
    Convert a TEI Facsimile to a format similar to Abbyy FineReader's XML
    output.

    Args:
        doc (unicode, unicode): Storage tuple of the input document

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    with storage.StorageFile(*doc) as fp:
        tei = OCRRecord()
        logger.debug('Reading TEI ({}/{})'.format(*doc))
        tei.load_tei(fp)
    output_path = storage.insert_suffix(doc[1], method)
    with storage.StorageFile(doc[0], output_path, 'wb') as fp:
        logger.debug('Writing abbyyxml to {}'.format(fp.abs_path))
        tei.write_abbyyxml(fp)
    return (doc[0], output_path)


@app.task(base=NidabaTask, name=u'nidaba.output.tei2hocr')
def tei2hocr(doc, method=u'tei2hocr'):
    """
    Convert a TEI Facsimile to hOCR preserving as much metadata as possible.

    Args:
        doc (unicode, unicode): Storage tuple of the input document

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    with storage.StorageFile(*doc) as fp:
        tei = OCRRecord()
        logger.debug('Reading TEI ({}/{})'.format(*doc))
        tei.load_tei(fp)
    output_path = storage.insert_suffix(doc[1], method)
    with storage.StorageFile(doc[0], output_path, 'wb') as fp:
        logger.debug('Writing hOCR to {}'.format(fp.abs_path))
        tei.write_hocr(fp)
    return (doc[0], output_path)


@app.task(base=NidabaTask, name=u'nidaba.output.tei2txt')
def tei2txt(doc, method=u'tei2txt'):
    """
    Convert a TEI Facsimile to a plain text file.

    Args:
        doc (unicode, unicode): Storage tuple of the input document

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    with storage.StorageFile(*doc) as fp:
        tei = OCRRecord()
        logger.debug('Reading TEI ({}/{})'.format(*doc))
        tei.load_tei(fp)
    output_path = storage.insert_suffix(doc[1], method)
    with storage.StorageFile(doc[0], output_path, 'wb') as fp:
        logger.debug('Writing text to {}'.format(fp.abs_path))
        tei.write_text(fp)
    return (doc[0], output_path)
