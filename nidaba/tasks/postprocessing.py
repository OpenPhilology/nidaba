# -*- coding: utf-8 -*-
"""
nidaba.tasks.postprocessing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Various postprocessing tasks that operate upon recognized texts.

"""

from __future__ import absolute_import, unicode_literals

from nidaba import storage
from nidaba import merge_hocr
from nidaba import lex
from nidaba.tasks.helper import NidabaTask
from nidaba.celery import app
from nidaba.config import nidaba_cfg


@app.task(base=NidabaTask, name=u'nidaba.postprocessing.spell_check')
def spell_check(doc, method=u'spell_check', language=u'',
                filter_punctuation=False, no_ocrx_words=u'auto'):
    """
    Adds spelling suggestions to an hOCR document. 

    Alternative spellings for each hocr ``ocrx_word`` span are created using
    the INS-DEL syntax defined for alternative readings in the hOCR
    specification. Correct words, i.e. words appearing verbatim in the
    dictionary, are left untouched; words not appearing in the dictionary and
    without suggestions will still be encoded as a 

    Args:
        doc (unicode, unicode): The input document tuple.
        method (unicode): The suffix string appended to the output file.
        language (unicode): Identifier defined in the nidaba configuration as a
                            valid dictionary.
        filter_punctuation (bool): Switch to filter punctuation inside
                                   ``ocrx_words``
        no_ocrx_words (unicode): Fallback switch to extract words from on hOCR
                                 document without ``ocrx_word`` elements. May
                                 be set to ``auto``, ``true``, or ``false``.

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method, language,
                                        filter_punctuation, no_ocrx_words)
    dictionary = nidaba_cfg['lang_dicts'][language][0]
    del_dictionary = nidaba_cfg['lang_dicts'][language][1]
    ret = lex.hocr_spellcheck(input_path, dictionary, del_dictionary,
                              filter_punctuation, no_ocrx_words)
    storage.write_text(*get_storage_path(output_path), text=ret)
    return get_storage_path(output_path)


@app.task(base=NidabaTask, name=u'nidaba.postprocessing.blend_hocr')
def blend_hocr(doc, method=u'blend_hocr', language=u''):
    """
    Blends multiple hOCR files using the algorithm from Bruce Robertsons
    rigaudon. It requires a working spell checking for the input document's
    language; otherwise all matched bboxes will be bunched together without any
    scoring.

    Args:
        doc [(id, path), ...]: A list of storage module tupels that will be
        merged into a single output document.
        language (unicode): Language used for spell-checking based scoring. If
                            not defined no scoring will be used.
        method (unicode): The suffix string appended to the output file.

    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    # create the output document path from the first input document
    input_path = storage.get_abs_path(*doc[0])
    output_path = storage.insert_suffix(input_path, method)
    return merge_hocr.merge(doc, language,
                            storage.get_storage_path(output_path))
