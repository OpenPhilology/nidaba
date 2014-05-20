# -*- coding: utf-8 -*-
# A spell checking class based on hunspell
import irisconfig
import storage
import uuid

from hunspell import HunSpell


class spellcheck():
    """
    A spell checker based on Hunspell.
    """

    def __init__(self, lang):
        if lang not in irisconfig.LANG_DICTS:
            # yes exceptions only accept byte strings
            raise ValueError((u'No dictionary defined for ' + lang).encode('utf-8'))
        try:
            dict_path = storage._sanitize_path(irisconfig.DICT_PATH, irisconfig.LANG_DICTS[lang][0])
        except Exception as err:
            raise ValueError(u'Dictionary path not valid.')

        # Hunspell always requires an affix file, but an empty one is valid.
        aff_path = storage._sanitize_path(irisconfig.DICT_PATH, irisconfig.DEFAULT_AFFIX)
        if len(irisconfig.LANG_DICTS[lang]) == 2:
            try:
                aff_path = storage._sanitize_path(irisconfig.DICT_PATH, irisconfig.LANG_DICTS[lang][1])
            except Exception as err:
                raise ValueError(u'Affix file path not valid.')
        try:
            self.h = HunSpell(dict_path.encode('utf-8'), aff_path.encode('utf-8'))
        except Exception as err:
            raise ValueError(u'Hunspell initialization failed.')

    def suggest(self, text, suggest_correct=False, count=5):
        """
        Spell checks a list of words (text). Returns at most count suggestions for
        each word (or as many as hunspell returns for 0). If suggest_correct is
        set, suggestions will be generated even for words the spell checker deems
        correct.
        The returned object is a list of tuples containing the original word and a
        list of possible alternatives.

        Note that words will be re-encoded to match the coding of the dictionary
        file, causing silent failure or erratic behavior. Keep everything in UTF-8
        and the FSM will be happy.
        """
        ret_list = []
        for word in text:
            # If your input and dictionary encoding do not match you're probably
            # screwed anyway so loss of information of perfectly acceptable.
            eword = word.encode(self.h.get_dic_encoding(), 'replace')
            if not suggest_correct and self.h.spell(eword):
                ret_list.append((word, []))
            else:
                s = [s.decode(self.h.get_dic_encoding()) for s in self.h.suggest(eword)]
                if count:
                    s = s[0:count]
                ret_list.append((word, s))
        return ret_list

    def spell(self, text):
        """
        Given a list of words, returns only the ones recognized as correct by
        the dictionary.
        """
        return [s for s in text if self.h.spell(s.encode(self.h.get_dic_encoding(), 'replace'))]
