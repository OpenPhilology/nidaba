# -*- coding: utf-8 -*-
"""
nidaba.tasks.postprocessing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Various postprocessing tasks that operate upon recognized texts.

"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba import storage
from nidaba import merge_hocr
from nidaba import lex
from nidaba.celery import app
from nidaba.tei import OCRRecord 
from nidaba.config import nidaba_cfg
from nidaba.tasks.helper import NidabaTask

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@app.task(base=NidabaTask, name=u'nidaba.postprocessing.spell_check', 
          arg_values={'language': nidaba_cfg['lang_dicts'].keys(),
                      'filter_punctuation': [True, False]})
def spell_check(doc, method=u'spell_check', language=u'',
                filter_punctuation=False):
    """
    Adds spelling suggestions to an TEI XML document.

    Alternative spellings for each segment will be included in a choice
    tagcontaining a series of corr tags with the original segment appearing
    beneath a sic element.  Correct words, i.e. words appearing verbatim in the
    dictionary, are left untouched.

    Args:
        doc (unicode, unicode): The input document tuple.
        method (unicode): The suffix string appended to the output file.
        language (unicode): Identifier defined in the nidaba configuration as a
                            valid dictionary.
        filter_punctuation (bool): Switch to filter punctuation inside
                                   ``seg``
    Returns:
        (unicode, unicode): Storage tuple of the output document
    """
    input_path = storage.get_abs_path(*doc)
    output_path = storage.insert_suffix(input_path, method, language,
                                        unicode(filter_punctuation))
    dictionary = storage.get_abs_path(*nidaba_cfg['lang_dicts'][language]['dictionary'])
    del_dictionary = storage.get_abs_path(*nidaba_cfg['lang_dicts'][language]['deletion_dictionary'])
    with storage.StorageFile(*doc) as fp:
        logger.debug('Reading TEI ({})'.format(fp.abs_path))
        tei = OCRRecord()
        tei.load_tei(fp)
        logger.debug('Performing spell check')
        ret = lex.tei_spellcheck(tei, dictionary, del_dictionary,
                                 filter_punctuation)
    with storage.StorageFile(*storage.get_storage_path(output_path), mode='wb') as fp:
        logger.debug('Writing TEI ({})'.format(fp.abs_path))
        ret.write_tei(fp)
    return storage.get_storage_path(output_path)


# @app.task(base=NidabaTask, name=u'nidaba.postprocessing.blend_hocr')
# def blend_hocr(doc, method=u'blend_hocr', language=u''):
#     """
#     Blends multiple hOCR files using the algorithm from Bruce Robertsons
#     rigaudon. It requires a working spell checking for the input document's
#     language; otherwise all matched bboxes will be bunched together without any
#     scoring.
#
#     Args:
#         doc [(id, path), ...]: A list of storage module tupels that will be
#         merged into a single output document.
#         language (unicode): Language used for spell-checking based scoring. If
#                             not defined no scoring will be used.
#         method (unicode): The suffix string appended to the output file.
#
#     Returns:
#         (unicode, unicode): Storage tuple of the output document
#     """
#     # create the output document path from the first input document
#     input_path = storage.get_abs_path(*doc[0])
#     output_path = storage.insert_suffix(input_path, method)
#     return merge_hocr.merge(doc, language,
#                             storage.get_storage_path(output_path))
