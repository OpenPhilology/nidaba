# -*- coding: utf-8 -*-
# A collection of common postprocessing tasks. 
import irisconfig
import uuid

from fs import path
from hunspell import HunSpell

def spell_check(lang, text, suggs = 0, suggest_correct = False):
    """
    Spell checks a list of words (text). Returns at most suggs suggestions for
    each word (or as many as hunspell returns for 0). If suggest_correct is
    set, suggestions will be generated even for words the spell checker deems
    correct. 
    The returned object is a list of tuples containing the original word and a
    list of possible alternatives.

    Note that words will be re-encoded to match the coding of the dictionary
    file, causing silent failure or erratic behavior. Keep everything in UTF-8
    and the FSM will be happy.
    """

    if lang not in irisconfig.LANG_DICTS:
        #print('No dictionary defined for ' + lang)
        return None
    
    try:
        dict_path = path.join(irisconfig.DICT_URL, irisconfig.LANG_DICTS[lang][0])
    except Exception as err:
        #print('Dictionary path not valid.')
        #print(err)
        return None

    # Hunspell always requires an affix file, but an empty one is valid.
    aff_path = '/dev/null'
    if len(irisconfig.LANG_DICTS[lang]) == 2:
        try:
            aff_path = path.join(irisconfig.DICT_URL, irisconfig.LANG_DICTS[lang][1])
        except Exception as err:
            #print('Affix file path not valid.')
            #print(err)
            return None
    
    try:
        h = HunSpell(dict_path, aff_path)
    except Exception as err:
        #print('Hunspell initialization failed.')
        #print(err)
        return None

    ret_list = []
    for word in text:
        # If your input and dictionary encoding do not match you're probably
        # screwed anyway so loss of information of perfectly acceptable.
        eword = word.encode(h.get_dic_encoding(), 'replace')
        if not suggest_correct and h.spell(eword):
            ret_list.append((word, []))
        else:
            s = h.suggest(eword)
            if suggs:
                s = s[0:suggs]
            ret_list.append((word, s))
    return ret_list
