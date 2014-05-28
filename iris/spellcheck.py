# -*- coding: utf-8 -*-
# A spell checking class based on hunspell
import irisconfig
import storage
import uuid
import ngram
import unicodedata

class spellcheck():
    """
    A ngram similarity spell checker.
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
            self.nset = ngram.NGram()
            with open(dict_path) as f:
                for line in f:
                    self.nset.add(unicodedata.normalize('NFC', line.decode('utf-8')).strip())
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
        ensure good results make sure input is in NFC.
        """
        ret_list = []
        for word in text:
            if not suggest_correct and word in self.nset:
                ret_list.append((word, []))
            else:
                s = [s[0] for s in self.nset.search(word)]
                if count:
                    s = s[0:count]
                ret_list.append((word, s))
        return ret_list

    def spell(self, text):
        """
        Given a list of words, returns only the ones recognized as correct by
        the dictionary.
        """
        return [s for s in text if s in self.nset]
