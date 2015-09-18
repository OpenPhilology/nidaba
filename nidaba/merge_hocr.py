# -*- coding: utf-8 -*-
"""
nidaba.merge_hocr
~~~~~~~~~~~~~~~~~

A naive algorithm merging multiple hOCR output documents into one.
"""

from __future__ import unicode_literals, print_function, absolute_import

from lxml import etree
from operator import attrgetter
from nidaba import storage


class Rect(object):
    """
    Native python replacement for gameras C++ Rect object.
    """

    def __init__(self, ul=(0, 0), lr=(0, 0)):
        self.ul = ul
        self.lr = lr
        self.lr_x = lr[0]
        self.lr_y = lr[1]
        self.ll_x = ul[0]
        self.ll_y = lr[1]
        self.ul_x = ul[0]
        self.ul_y = ul[1]
        self.ur_x = lr[0]
        self.ur_y = ul[1]


class hocrWord(object):
    """
    Dummy class associating word text with a bbox.
    """


class hocrLine(object):
    """
    Dummy class associating lines, words with their text and bboxes.
    """


def parse_bbox(prop_str):
    """
    Parses the microformat property string in the hOCR title field.

    Args:
        prop_str (unicode): The verbatim property string

    Returns:
        Rect: A rectangular area described in a bbox field

    Raises:
        ValueError: The property string either did not contain a bbox
                    definition or this definition was malformed.
    """
    for prop in prop_str.split(';'):
        p = prop.split()
        if p[0] == 'bbox':
            return Rect((p[1], p[2]), (p[3], p[4]))
        else:
            continue
    raise ValueError('bounding box not in proper format')


def get_hocr_lines_for_tree(treeIn):
    hocr_line_elements = treeIn.xpath("//html:span[@class='ocr_line'] |\
                                      //span[@class='ocr_line']",
                                      namespaces={'html':
                                                  "http://www.w3.org/1999/xhtml"})
    line_counter = 0
    lines_out = []
    all_words = []
    for hocr_line_element in hocr_line_elements:
        line_counter += 1
        words = hocr_line_element.xpath(".//html:span[@class='ocr_word'] |\
                                        .//span[@class='ocr_word'] ",
                                        namespaces={'html':
                                                    "http://www.w3.org/1999/xhtml"})
        words_out = []
        for word in words:
            aWord = hocrWord()
            aWord.text = ""
            if word.text:
                aWord.text += word.text
            # get rid of any inner elements, and just keep their text values
            for element in word.iterchildren():
                if element.text:
                    aWord.text += element.text
                word.remove(element)
            # set the contents of the xml element to the stripped text
            word.text = aWord.text
            aWord.bbox = parse_bbox(word.get('title'))
            aWord.element = word
            words_out.append(aWord)
        aLine = hocrLine()
        all_words = all_words + words_out
        aLine.words = words_out
        aLine.element = hocr_line_element
        aLine.bbox = parse_bbox(hocr_line_element.get('title'))
        lines_out.append(aLine)
    return lines_out, all_words


def close_enough(bbox1, bbox2, fudge=0.1):
    """
    Roughly matches two bboxes roughly using a fudge factor.

    Args:
        bbox1 (Rect): Rect object of a bounding box.
        bbox2 (Rect): Rect object of a bounding box.
        fudge (float): Fudge factor to account for slight variations in word
                       boundary detection between segmentation engines.

    Returns:
        bool: True if the bounding boxes are sufficiently aligned, False
        otherwise.
    """
    total_circum1 = (bbox1.lr_x - bbox1.ul_x) * 2 + \
        (bbox1.lr_y - bbox1.ul_y) * 2
    total_circum2 = (bbox1.lr_x - bbox1.ul_x) * 2 + \
        (bbox1.lr_y - bbox1.ul_y) * 2
    f = (total_circum1 + total_circum2) * fudge
    total_diff = (abs(bbox1.lr_x - bbox2.lr_x) + abs(bbox1.lr_y - bbox2.lr_y) +
                  abs(bbox1.ul_x - bbox2.ul_x) + abs(bbox1.ul_y - bbox2.ul_y))
    if total_diff < f:
        return True
    else:
        return False


def sort_words_bbox(words):
    """
    Sorts word bboxes of a document in European reading order (upper left to
    lower right). The list is sorted in place.

    Args:
        words (list): List of hocrWord object containing Rects in the field
                      bbox and the recognized text in the text field.

    Returns:
        list: The sorted word list.
    """
    words.sort(key=attrgetter('bbox.lr_y'))
    words.sort(key=attrgetter('bbox.lr_x'))
    words.sort(key=attrgetter('text'))
    return words


def score_word(lang, word):
    """
    A simple token scoring function similar to the one used in Bruce Robertsons
    rigaudon. FIXME: Actually score input tokens.

    Args:
        lang (unicode): Language to use for scoring.
        word (unicode): Input token to score

    Returns:
        int: Value representing the input tokens score. Higher values are
             closer to native language words.
    """
    # IN_DICT_SCORE = 1000
    # IN_DICT_LOWER_SCORE = 100
    # CAMEL_CASE_SCORE = 1
    # ALL_CAPS_SCORE = 10
    score_total = 0
    # no language => no score
    if not lang:
        return score_total
    # if spell(lang, word):
    #     score_total = score_total + IN_DICT_SCORE
    # elif spell(lang, word.lower()):
    #     score_total = score_total + IN_DICT_LOWER_SCORE
    # if score_total > 0:
    #     if word.istitle():
    #         score_total = score_total + CAMEL_CASE_SCORE
    #     elif word.isupper():
    #         score_total = score_total + ALL_CAPS_SCORE
    return score_total


def merge(docs, lang, output):
    """
    Merges multiple hOCR documents into a single one.

    First bboxes from all documents are roughly matched, then all matching
    bboxes are scored using a spell checker. If no spell checker is available
    all matches will be merged without ranking.

    The matching is naive, i.e. we just grab the first input document and
    assume that all other documents have similar segmentation results. Issues
    like high variance in segmentation, especially word boundaries are not
    accounted for.

    Args:
        docs (iterable): A list of storage tuples of input documents
        lang (unicode): A language identifier for the spell checker
        output (tuple): Storage tuple for the result

    Returns:
        tuple: The output storage tuple. Should be the same as ```output```.
    """
    parser = etree.HTMLParser()
    tree1 = etree.parse(storage.get_abs_path(docs[0][0], docs[0][1]), parser)
    lines_1, words_1 = get_hocr_lines_for_tree(tree1)
    sort_words_bbox(words_1)
    other_words = []
    for doc in docs[1:]:
        try:
            tree2 = etree.parse(storage.get_abs_path(doc[0], doc[1]), parser)
            lines_2, words_2 = get_hocr_lines_for_tree(tree2)
            other_words = other_words + words_2
        except Exception as e:
            print(e)

    sort_words_bbox(other_words)
    positional_lists = []
    positional_list = []
    x = 0

    # Make a list of positional_lists, that is alternatives for a given
    # position, skipping duplicate position-words
    while x < len(other_words):
        try:
            if len(positional_list) == 0:
                positional_list.append(other_words[x])
            else:
                if close_enough(other_words[x - 1].bbox, other_words[x].bbox):
                    # skip if the text is the same, so that we just get unique
                    # texts for this position
                    if not other_words[x - 1].text == other_words[x].text:
                        positional_list.append(other_words[x])
                else:
                    if not x == 0:
                        positional_lists.append(positional_list)
                        positional_list = []
        except IndexError:
            pass
        x = x + 1

    # we now have a list of list of unique words for each position
    # let's select from each the first one that passes spellcheck
    replacement_words = []

    # make a 'replacement_words' list with all of the best, non-zero-scoring
    # suggestions for each place
    for positional_list in positional_lists:
        for word in positional_list:
            word.score = score_word(lang, word.text)
        positional_list.sort(key=attrgetter('score'), reverse=True)
        if positional_list[0].score > 0:
            replacement_words.append(positional_list[0])

    # now replace the originals
    for word in words_1:
        for replacement_word in replacement_words:
            word.score = score_word(lang, word.text)
            if close_enough(word.bbox, replacement_word.bbox) and (
                    word.score < replacement_word.score):
                word.element.text = replacement_word.text

        for positional_list in positional_lists:
            print("##")
            for word in positional_list:
                print(word.bbox, word.text)

    storage.write_text(*output, text=etree.tostring(tree1.getroot(),
                                                    encoding='unicode'))
    return output
