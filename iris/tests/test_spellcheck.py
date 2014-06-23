# -*- coding: utf-8 -*-
import unittest
import storage
import uuid
from fs import utils,path
from postprocessing import spell_check

class SpellCheckTests(unittest.TestCase):
    '''
    Tests the spell checker of the postprocessing framework. 
    '''

    def test_correct_word(self):
        '''Tests if correct words are recognized.'''
        self.assertEqual([('bacru', [])], spell_check('lojban', [u'bacru']))

    def test_correct_word_sugg(self):
        '''Tests if alternatives for correct words are returned.'''
        self.assertEqual([(u'bacru', ['bacru'])], spell_check('lojban', [u'bacru'], suggest_correct=True))

    def test_dictionary_mismatch(self):
        '''Tests if mismatch encoding for word and dictionary are recognized.'''
        pass

    def test_invalid_lang(self):
        '''Tests if non-defined languages are recognized.'''
        self.assertIsNone(spell_check('esperanto', [u'pardonu']))

    def test_multiple_word(self):
        '''Tests if multiple word spell checking is done correctly.'''
        wlist = [ u'bacru', u'bucr', u'badr', u'budr' ]
        pass

if __name__ == '__main__':
    unittest.main()
