=============
Option Groups
=============

.. _bin:

Binarization
============

`Binarization
<http://en.wikipedia.org/wiki/Thresholding_%28image_processing%29>`_ is the
process of converting a grayscale image to a bi-level image by selecting one or
more thresholds separating foreground (usually the text to be recognized) from
background (usually the white page) pixels. As all character recognition
methods implemented in nidaba operate only on bi-level images, it is paramount
to create properly binarized images as a preprocessing step.

Binarization is an own group of tasks and functions can be accessed using the
``--binarization/-b`` switch:

.. code-block:: console

    $ nidaba batch ... -b otsu -b sauvola ... -- *.tif

Options and Syntax
------------------

.. autofunction:: nidaba.tasks.binarize.otsu(doc, method=u'spell_check')

There are also additional, more advanced binarization algorithms available in
the :mod:`leptonica <nidaba.plugins.leptonica>` and :mod:`kraken
<nidaba.plugins.kraken>` plugins.


.. _segmentation_heading:

Page Segmentation
=================

A prerequisite to the actual OCR is the extraction of textual elements,
columns, paragraphs, and lines, from the page. Page segmentation is a separate
group of tasks and functions can be accessed using the ``--segmentation/-l``
switch:

.. code-block:: console

    # nidaba batch ... -l kraken -l tesseract ... -- *.tif

Options and Syntax
------------------

Segmentation is usually an integral part of an OCR engine, so different
implementations are situated in their respective plugins. See :mod:`tesseract
<nidaba.plugins.tesseract>` and :mod:`kraken <nidaba.plugins.kraken>` for
additional information.


.. _ocr_heading:

Optical Character Recognition
=============================

`OCR <http://en.wikipedia.org/wiki/Optical_character_recognition>`_ is arguably
the main part of nidaba. Currently 3 OCR engines are implemented and can be
accessed using the ``--ocr`` group of task:

.. code-block:: console

    $ nidaba batch ... -o tesseract:eng -o kraken:en-default ... -- *.tif

Options and Syntax
------------------

As OCR engines are usually quite large and sometimes hard to install, all
functionality is contained in plugins. See :mod:`tesseract
<nidaba.plugins.tesseract>`, :mod:`kraken <nidaba.plugins.kraken>`, and
:mod:`ocropus <nidaba.plugins.ocropus>` for additional information,
configuration keys, etc.

.. _spell-checking:

Spell Checking
==============

Nidaba includes support for an edit distance based spell checker out of the
box. Particular configurations of the spell checking algorithm have to be
predefined in the ``nidaba.yaml`` configuration file under the ``lang_dicts``
section:

.. code-block:: yaml

    lang_dicts:
      polytonic_greek: {dictionary: [dicts, greek.dic],
                        deletion_dictionary: [dicts, del_greek.dic]}
      latin: {dictionary: [dicts, latin.dic],
                        deletion_dictionary: [dicts, del_latin.dic]}

The spell-checker is part of the postprocessing group of tasks and can be
accessed be the name ``spell_check``, e.g.:

.. code-block:: console

    $ nidaba batch ... -p spell_check:polytonic_greek ... -- *.tif

Creating Dictionaries
---------------------

The spell checker requires two dictionaries on the common storage medium: a
dictionary of valid word forms and a corresponding file containing a mapping
between variants and those valid word forms. Both are best created using the
``nidaba_mkdict`` tool installed by the default distribution. It takes a
arbitrary text document, extracts all unique character sequences, and
calculates the dictionaries in a normalized format. For example:

.. code-block:: console

    $ nidaba_mkdict --input greek.txt --del_dict del_greek.dic --dictionary greek.dic
    Reading input file      [✓]
    Writing dictionary      [✓]
    Writing deletions       [✓]

Be aware that calculating the deletion dictionary is a process requiring a lot
of memory, e.g. for a 31Mb word list mkdict utilizes around 8Gb memory and the
resulting deletion dictionary will be 750Mb large.

Options and Syntax
------------------

.. autofunction:: nidaba.tasks.postprocessing.spell_check(doc, method, language, filter_punctuation, no_ocrx_words)


.. _merging:

Output Merging
==============

There is a rudimentary merging algorithm able to combine multiple recognition
results into a single document if certain conditions are met. The combined
output can then be used for further postprocessing, e.g manual correction or
lexicality based weighting. It has been ported from Bruce Robertson's
`rigaudon <https://github.com/brobertson/rigaudon>`_, an OCR engine for
polytonic Greek.

Currently, its basic operation is as follows. First (word) bboxes from all
documents are roughly matched, then all matching bboxes are scored using a
spell checker. If no spell checker is available all matches will be merged
without ranking.

.. note::

        The matching is naive, i.e. we just grab the first input document and
        assume that all other documents have similar segmentation results.
        Issues like high variance in segmentation, especially word boundaries
        are not accounted for.
       
Options and Syntax
------------------

.. autofunction:: nidaba.tasks.postprocessing.blend_hocr(doc, method, language)

.. _metrics:

Metrics
=======

.. _output_layer:

Output Layer
============

The output layer handles conversion and extension of nidaba's native :ref:`TEI
<tei_output>` format. It can be used to distill data from the TEI document into
plain text, hOCR, and a simple XML format. It can also use an external metadata
file to complete raw TEI output to a valid TEI document.

Options and Syntax
------------------

.. autofunction:: nidaba.tasks.output.tei_metadata(doc, method, metadata, validate)
.. autofunction:: nidaba.tasks.output.tei2simplexml(doc, method)
.. autofunction:: nidaba.tasks.output.tei2hocr(doc, method)
.. autofunction:: nidaba.tasks.output.tei2txt(doc, method)
