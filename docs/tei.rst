.. _tei_output:

==========
TEI Output
==========

`TEI <http://www.tei-c.org/>`_ is a consortium maintaining standards for the
representation of texts in digital form which are widely used in the
humanities. Nidaba is capable of encoding the OCR results and their metadata
into XML documents following the most recent `P5 guidelines
<http://www.tei-c.org/Guidelines/P5/>`_. The output is designed to facilitate
further manual annotation.

Format
======

Fundamentally output is generated following the `embedded transcription
<http://www.tei-c.org/release/doc/tei-p5-doc/en/html/PH.html#PHZLAB>`_ scheme
with a single surface containing all recognized line elements with their
textual representation.

The (body) skeleton of a TEI-OCR file will look like this:

.. code-block:: xml

    <sourceDoc>
        <surface ulx="0" uly="0" lrx="500" lry="500">
            <graphic url="foo.png"/>
            <zone>
                <line ulx=a uly=b lrx=c lry=d resp="#resp_0">
                    <zone lrx="1028" lry="182" type="segment" ulx="593" uly="119" xml:id="seg_0" resp="#resp_1">
                        <zone lrx="629" lry="182" resp="#resp_1" type="grapheme" ulx="593" uly="119">
                            <seg>
                                <g xml:id="grapheme_0" resp="#resp_1">5</g>
                            </seg>
                            <certainty degree="0.83" locus="value" target="#grapheme_0" resp="#resp_1"/>
                        </zone>
                        <zone lrx="1028" lry="182" resp="#resp_1" type="grapheme" ulx="629" uly="119">
                            <seg>
                                <g xml:id="grapheme_1" resp="#resp_1">4</g>
                            </seg>
                            <certainty degree="0.99" locus="value" target="#grapheme_1" resp="#resp_1"/>
                        </zone>
                    </zone>
                    <zone lrx="1066" lry="182" resp="#resp_1" type="grapheme" ulx="1028" uly="119">
                        <seg>
                            <g xml:id="grapheme_2" resp="#resp_1"> </g>
                        </seg>
                        <certainty degree="0.97" locus="value" target="#grapheme_2" resp="#resp_1"/>
                    </zone>
                    <zone lrx="1199" lry="182" type="segment" ulx="1066" uly="119" xml:id="seg_1" resp="#resp_1">
                    ...
                    </zone>
                </line>
                <line ulx=a uly=b lrx=c lry=d>
                ...
                </line>
            </zone>
        </surface>
    </sourceDoc>

.. note::
    The `g <http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-g.html>`_
    tag does NOT encode single characters but entities fed into the character
    recognition engine. These entities are called `grapheme clusters
    <http://www.unicode.org/reports/tr29/>`_ and may correspond to a single
    character/codepoint, multiple codepoints or in the case of ligatures
    decomposited by the engine even to multiple characters (œ to oe).

Header
======

Most of the TEI header is filled using the
:py:func:`nidaba.tasks.output.tei_metadata` task.

Attribution
===========

The source of a particular element is usually attributed using a series of
`respStmt
<http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-respStmt.html>`_ block
in the header of the document. A common example encoding a page segmentation
and character recognition as two sources of data in the document will resemble
these two statements:

.. code-block:: xml

    <respStmt xml:id="resp_0">
        <resp>page segmentation</resp>
        <name>tesseract</name>
    </respStmt>
    <respStmt xml:id="resp_1">
        <resp>character recognition</resp>
        <name>kraken</name>
    </respStmt>

Elements themselves are linked to these statements using the `resp
<http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-att.global.responsibility.html#tei_att.resp>`_
attribute:

.. code-block:: xml

    <g xml:id="grapheme_9" resp="#resp_1">x</g>

When merging the output of multiple OCR engines diverging ``readings`` will
also be attributed to their origin using the ``respStmt`` tag. Alternative
spellings provided by a spell checker will also be properly attributed.

Certainty
=========

Some recognition results will have a confidence value using the certainty tag
associated with them:

.. code-block:: xml

    <zone lrx="526" lry="291" resp="#resp_1" type="grapheme" ulx="422" uly="225">
        <seg>
            <g xml:id="grapheme_0" resp="#resp_1">Μ</g>
        </seg>
        <certainty degree="0.76" locus="value" target="#grapheme_0" resp="#resp_1"/>
    </zone>

These necessarily refer to the identifier of the targeted element using the
``target`` attribute. The probability is a float value between 0 and 1 with
higher values indicating higher confidence in the results.
