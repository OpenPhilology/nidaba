# -*- coding: utf-8 -*-
# A spell checking class based on hunspell
import irisconfig
import storage
import uuid
import cPickle
import unicodedata

from algorithms import sym_suggest

class spellcheck():
    """
    A spell checker utilizing the symmetric edit distance algorithm.
    """

    def __init__(self, lang):
        if lang not in irisconfig.LANG_DICTS:
            # yes exceptions only accept byte strings
            raise ValueError((u'No dictionary defined for ' + lang).encode('utf-8'))
        try:
            dict_path = storage._sanitize_path(irisconfig.DICT_PATH, irisconfig.LANG_DICTS[lang])
        except Exception as err:
            raise ValueError(u'Dictionary path not valid.')

        try:
            with open(dict_path) as f:
                st = cPickle.load(f)
                self.dic = st[u'dictionary']
                self.ed = st[u'edit_distance']
        except Exception as err:
            raise ValueError((u'Spellcheck initialization failed: ' + unicode(err)).encode('utf-8'))

    def suggest(self, text, suggest_correct=False, count=5):
        """
        Spell checks a list of words (text). Returns at most count suggestions for
        each word (or all matches for 0). If suggest_correct is
        set, suggestions will be generated even for words the spell checker deems
        correct.
        The returned object is a list of tuples containing the original word and a
        list of possible alternatives.
        The spell checker is highly sensitive to unicode normalization; to
        ensure good results make sure input is in NFD.
        """
        ret_list = []
        for word in text:
            if not suggest_correct and word in self.dic.iterkeys():
                ret_list.append((word, []))
            else:
                s = [s[0] for s in sym_suggest(word, self.dic, self.ed, count)]
                if count:
                    s = s[0:count]
                ret_list.append((word, s))
        return ret_list

    def spell(self, text):
        """
        Given a list of words, returns only the ones recognized as correct by
        the dictionary.
        """
        ret = []
        for word in text:
            suggestions = sym_suggest(word, self.dic, 0)
            for s in suggestions:
                if s[1] == 0:
                    ret.append(word)
                    break
        return ret
