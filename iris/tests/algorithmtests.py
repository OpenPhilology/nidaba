# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import algorithms
import numpy
import StringIO
import unicodedata

thisfile = os.path.abspath(os.path.dirname(__file__))
resources = os.path.abspath(os.path.join(thisfile, 'resources/tesseract'))

# class OptimizedLevenshteinTests(unittest.TestCase):
#     """Tests the optimized edit distance algorithm by checking the resultant edit distance, but not the internal matrix, as this is not stored.
#     Tests are identical to those for the full Levenshtein tests where applicable."""

#     def test_equal_strings(self):
#         """Test the edit distance of identical strings"""
#         self.assertEqual(0, algorithms.edit_distance('test_string', 'test_string'))

#     def test_single_insert(self):
#         """Test with strings requiring one insert"""
#         self.assertEqual(1, algorithms.edit_distance('', 'a'))

#     def test_tenfold_insert(self):
#         """Test with strings requiring ten inserts"""
#         self.assertEqual(10, algorithms.edit_distance('', 'aaaaaaaaaa')) # A string with 10 a's.

#     def test_single_delete(self):
#         """Test with strings requiring one delete"""
#         self.assertEqual(1, algorithms.edit_distance('a', ''))

#     def test_tenfold_delete(self):
#         """Test with strings requiring ten deletes"""
#         self.assertEqual(10, algorithms.edit_distance('aaaaaaaaaa', '')) # A string with 10 a's.

#     def test_singledelete_singleadd(self):
#         """Test with strings requiring a single non-trivial insert."""
#         self.assertEqual(2, algorithms.edit_distance('abbb', 'bbbbb')) # Should delete the a and insert the final b.

#     def test_singleadd_singledelete(self):
#         """Test with strings requiring a single non-trivial delete."""
#         self.assertEqual(2, algorithms.edit_distance('bbbbb', 'abbb')) # Should delete the a and add the final b.

class LevenshteinTests(unittest.TestCase):
    """Tests the edit_distance funtion by checking both the edit distance and full matrix comparisons."""

    # -------------------------------------------------------------------
    # Edit distance tests -----------------------------------------------
    # -------------------------------------------------------------------

    def test_equal_strings(self):
        """
        Test the edit distance of identical strings
        """
        self.assertEqual(0, algorithms.edit_distance('test_string', 'test_string'))

    def test_single_insert(self):
        """
        Test with strings requiring one insert
        """
        self.assertEqual(1, algorithms.edit_distance('', 'a'))

    def test_tenfold_insert(self):
        """
        Test with strings requiring ten inserts
        """
        self.assertEqual(10, algorithms.edit_distance('', 'aaaaaaaaaa')) # A string with 10 a's.

    def test_single_delete(self):
        """
        Test with strings requiring one delete
        """
        self.assertEqual(1, algorithms.edit_distance('a', ''))

    def test_tenfold_delete(self):
        """
        Test with strings requiring ten deletes
        """
        self.assertEqual(10, algorithms.edit_distance('aaaaaaaaaa', '')) # A string with 10 a's.

    def test_singledelete_singleadd(self):
        """
        Test with strings requiring a single non-trivial insert.
        """
        self.assertEqual(2, algorithms.edit_distance('abbb', 'bbbbb')) # Should delete the a and insert the final b.

    def test_singleadd_singledelete(self):
        """
        Test with strings requiring a single non-trivial delete.
        """
        self.assertEqual(2, algorithms.edit_distance('bbbbb', 'abbb')) # Should delete the a and add the final b.    


    # -------------------------------------------------------------------
    # Score matrix tests ------------------------------------------------
    # -------------------------------------------------------------------

    def test_match_delete_matrix(self):
        """
        Test the scoring matrix state in an edit requiring one match and delete.
        """
        expected = [[0,1,2],[1,0,1]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('a', 'ab')[0])

    def test_match_insert_matrix(self):
        """
        Test the scoring matrix state in an edit requiring one match an insert.
        """
        expected = [[0,1],[1,0],[2,1]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('ab', 'a')[0])

    def test_all_match_matrix(self):
        """
        Test the scoring matrix state in an edit consisting only of multiple matches.
        """
        expected = [[0,1,2,3,4,5],
                    [1,0,1,2,3,4],
                    [2,1,0,1,2,3],
                    [3,2,1,0,1,2],
                    [4,3,2,1,0,1],
                    [5,4,3,2,1,0]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('aaaaa', 'aaaaa')[0])


    def test_all_subtitute_matrix(self):
        """
        Test the scoring matrix state in an edit consisting only of multiple substitutes.
        """
        expected = [[0,1,2,3,4,5],
                    [1,1,2,3,4,5],
                    [2,2,2,3,4,5],
                    [3,3,3,3,4,5],
                    [4,4,4,4,4,5],
                    [5,5,5,5,5,5]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('aaaaa', 'bbbbb')[0])

    def test_all_insert(self):
        """
        Test the scoring matrix state in an edit consisting only of multiple inserts.
        """
        expected = [[0,1,2,3,4,5]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('', 'abcde')[0])

    def test_all_delete(self):
        """
        Test the scoring matrix state in an edit consisting only of deletes.
        """
        expected = [[0],
                    [1],
                    [2],
                    [3],
                    [4],
                    [5]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('abcde', '')[0])

    def test_all_empty(self):
        """
        Test the scoring matrix state in an edit between two empty strings.
        """
        # expected = numpy.zeros(shape=(1,1))
        expected = [[0]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('', '')[0])


    # -------------------------------------------------------------------
    # Parameter tests ---------------------------------------------------
    # -------------------------------------------------------------------

    def test_substitution_parameter(self):
        """
        Test the functionality of the substitution score parameter.
        """
        default = algorithms.edit_distance('a', 'b')
        same_as_default = algorithms.edit_distance('a', 'b', substitutionscore=1)
        with_parameter = algorithms.edit_distance('a', 'b', substitutionscore=-7)
        with_parameter_and_max = algorithms.edit_distance('a', 'b', substitutionscore=7)
        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_deletion_parameter(self):
        """
        Test the functionality of the delete score parameter.
        """
        default = algorithms.edit_distance('a', '')
        same_as_default = algorithms.edit_distance('a', '', deletescore=1)
        with_parameter = algorithms.edit_distance('a', '', deletescore=-7)

        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_insertion_parameter(self):
        """
        Test the functionality of the insert score parameter.
        """
        default = algorithms.edit_distance('', 'a')
        same_as_default = algorithms.edit_distance('', 'a', insertscore=1)
        with_parameter = algorithms.edit_distance('', 'a', insertscore=-7)

        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_charmatrix_one_character_substitution_lower(self):
        """
        Test the functionality of the charmatrix parameter where in reduces the score of a substitution.
        """
        charmatrix = {('a', 'b'):0}
        expected = [[0,1],
                    [1,0]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('a', 'b', charmatrix=charmatrix)[0])

    def test_charmatrix_one_character_substitution_higher(self):
        """
        Test the functionality of the charmatrix parameter where in increases the score of a substitution.
        """
        charmatrix = {('a', 'b'):5}
        expected = [[0,1],
                    [1,5]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('a', 'b', charmatrix=charmatrix)[0])

    def test_charmatrix_one_character_substitution_default(self):
        """
        Test the functionality of the charmatrix parameter where it does not change a character score.
        """
        charmatrix = {('a', 'b'):1}
        expected = [[0,1],
                    [1,1]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('a', 'b', charmatrix=charmatrix)[0])


    def test_charmatrix_default_delete(self):
        """
        Test the case where the charmatrix mutates the score of trivial (first column) deletes.
        """
        charmatrix = {('', 'a'):5}
        expected = [[0],
                    [5],
                    [10],
                    [15]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('aaa', '', charmatrix=charmatrix)[0])

    def test_charmatrix_default_insert(self):
        """
        Test the case where the charmatrix mutates the score of trivial (first row) inserts.
        """
        charmatrix = {('a', ''):5}
        expected = [[0,5,10,15]]
        self.assertEqual(expected, algorithms.native_full_edit_distance('', 'aaa', charmatrix=charmatrix)[0])

    # -------------------------------------------------------------------
    # Word tests --------------------------------------------------------
    # -------------------------------------------------------------------


    def test_identical_word(self):
        self.assertEqual(0, algorithms.edit_distance(['word'], ['word']))
    
    def test_word_substitution(self):
        self.assertEqual(1, algorithms.edit_distance(['word'], ['different word']))

    def test_word_insertion(self):
        self.assertEqual(1, algorithms.edit_distance([], ['word']))

    def test_word_deletion(self):
        self.assertEqual(1, algorithms.edit_distance(['word'], []))

    def test_word_multi_insert(self):
        self.assertEqual(5, algorithms.edit_distance([], ['word', 'word', 'word', 'word', 'word']))

    def test_word_multi_delete(self):
        self.assertEqual(5, algorithms.edit_distance(['word', 'word', 'word', 'word', 'word'], []))

    def test_word_multi_match(self):
        self.assertEqual(0, algorithms.edit_distance(['word1', 'word2', 'word3'], ['word1', 'word2', 'word3']))

    def test_word_multi_substitute(self):
        self.assertEqual(3, algorithms.edit_distance(['word1', 'word2', 'word3'], ['otherword1', 'otherword2', 'otherword3']))


class AlignmentTests(unittest.TestCase):

    def test_empty_strings(self):
        """
        Tests the edit steps between two empty strings.
        """
        self.assertEqual([], algorithms.native_align('', ''))
    
    def test_insertions(self):
        """
        Test the edit steps when only inserts are needed.
        """
        self.assertEqual(['i', 'i', 'i', 'i', 'i'], algorithms.native_align('', 'abcde'))

    def test_deletions(self):
        """
        Test the edit steps when only deletes are needed.
        """
        self.assertEqual(['d', 'd', 'd', 'd', 'd'], algorithms.native_align('abcde', ''))
        
    def test_matches(self):
        """
        Test the edit steps when only matches are needed.
        """
        self.assertEqual(['m', 'm', 'm', 'm', 'm'], algorithms.native_align('abcde', 'abcde'))

    def test_matches_1(self):   #TODO
        """
        Test the edit steps when only substitutions are needed.
        """
        self.assertEqual(['s', 's', 's', 's', 's'], algorithms.native_align('abcde', 'vwxyz'))

    def test_wikepedia_example_1(self):
        """
        Test against the first general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm
        """
        self.assertEqual(['s', 'm', 'm', 'm', 's', 'm', 'd'], algorithms.native_align('sitting', 'kitten'))

    def test_wikepedia_example_2(self):
        """
        Test against the second general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm
        """
        self.assertEqual(['m', 'i', 'i', 'm', 's', 'm', 'm', 'm'], algorithms.native_align('sunday', 'saturday'))

class SemiGlobalAlignmentTests(unittest.TestCase):
    """
    Tests the semi_global_align function.
    """

    def test_sequence_length_inversion(self):
        """
        Test that an exception is thrown if the first sequence is > the second.
        """
        self.assertRaises(algorithms.AlgorithmException, algorithms.native_semi_global_align, 'abcdefghi', '') #Test with a long string
        self.assertRaises(algorithms.AlgorithmException, algorithms.native_semi_global_align, 'a', '') # Test with one character
        self.assertRaises(algorithms.AlgorithmException, algorithms.native_semi_global_align, ['word'], []) # Test with one word
        self.assertRaises(algorithms.AlgorithmException, algorithms.native_semi_global_align, ['word1', 'word2', 'word3'], ['word']) # Test with one word

    def test_identical(self):
        """
        Test with strings and lists of equal length.
        """
        expected = ['m']
        self.assertEqual(expected, algorithms.native_semi_global_align('a', 'a'))
        self.assertEqual(expected, algorithms.native_semi_global_align(['a'], ['a']))

    def test_identical_long(self):
        """
        Test with a longer series of matches.
        """
        expected = ['m', 'm', 'm', 'm', 'm']
        self.assertEqual(expected, algorithms.native_semi_global_align('abcde', 'abcde'))

    def test_identical_words(self):
        """
        Test with a series of of matching words.
        """
        expected = ['m', 'm', 'm', 'm', 'm']
        self.assertEqual(expected, algorithms.native_semi_global_align(['word1', 'word2', 'word3', 'word4', 'word5'], ['word1', 'word2', 'word3', 'word4', 'word5']))

    def test_simple_prefix(self):
        """
        Test with a single match and a skippable prefix.
        """
        expected = ['i', 'i', 'i', 'i', 'm']
        self.assertEqual(expected, algorithms.native_semi_global_align('b', 'aaaab'))

    def test_prefix_with_trailer(self):
        """
        Test with a single match and a skippable prefix and trailer.
        """
        expected = ['i', 'i', 'i', 'i', 'm']
        self.assertEqual(expected, algorithms.native_semi_global_align('b', 'aaaabcccc'))

    def test_word_prefix(self):
        """
        Test a list of words with a prefix.
        """
        expected = ['i', 'i', 'm']
        self.assertEqual(expected, algorithms.native_semi_global_align(['match'], ['w1', 'w2', 'match']))


class NumpyLevenshteinTests(unittest.TestCase):
    """
    Tests the np_full_edit_distance funtion by checking both the edit distance and full matrix comparisons.
    """

    # -------------------------------------------------------------------
    # Edit distance tests -----------------------------------------------
    # -------------------------------------------------------------------

    def test_equal_strings(self):
        """
        Test the edit distance of identical strings
        """
        self.assertEqual(0, algorithms.np_full_edit_distance('test_string', 'test_string')[0][-1,-1])

    def test_single_insert(self):
        """
        Test with strings requiring one insert
        """
        self.assertEqual(1, algorithms.np_full_edit_distance('', 'a')[0][-1,-1])

    def test_tenfold_insert(self):
        """
        Test with strings requiring ten inserts
        """
        self.assertEqual(10, algorithms.np_full_edit_distance('', 'aaaaaaaaaa')[0][-1,-1]) # A string with 10 a's.

    def test_single_delete(self):
        """
        Test with strings requiring one delete
        """
        self.assertEqual(1, algorithms.np_full_edit_distance('a', '')[0][-1,-1])

    def test_tenfold_delete(self):
        """
        Test with strings requiring ten deletes
        """
        self.assertEqual(10, algorithms.np_full_edit_distance('aaaaaaaaaa', '')[0][-1,-1]) # A string with 10 a's.

    def test_singledelete_singleadd(self):
        """
        Test with strings requiring a single non-trivial insert.
        """
        self.assertEqual(2, algorithms.np_full_edit_distance('abbb', 'bbbbb')[0][-1,-1]) # Should delete the a and insert the final b.

    def test_singleadd_singledelete(self):
        """
        Test with strings requiring a single non-trivial delete.
        """
        self.assertEqual(2, algorithms.np_full_edit_distance('bbbbb', 'abbb')[0][-1,-1]) # Should delete the a and add the final b.    

    # -------------------------------------------------------------------
    # Score matrix tests ------------------------------------------------
    # -------------------------------------------------------------------

    def test_match_delete_matrix(self):
        """
        Test the scoring matrix state in an edit requiring one match and delete.
        """
        expected = numpy.array([[0,1,2],[1,0,1]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('a', 'ab')[0]))

    def test_match_insert_matrix(self):
        """
        Test the scoring matrix state in an edit requiring one match an insert.
        """
        expected = numpy.array([[0,1],[1,0],[2,1]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('ab', 'a')[0]))

    def test_all_match_matrix(self):
        """
        Test the scoring matrix state in an edit consisting only of multiple matches.
        """
        expected = numpy.array([[0,1,2,3,4,5],
                                [1,0,1,2,3,4],
                                [2,1,0,1,2,3],
                                [3,2,1,0,1,2],
                                [4,3,2,1,0,1],
                                [5,4,3,2,1,0]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('aaaaa', 'aaaaa')[0]))


    def test_all_subtitute_matrix(self):
        """
        Test the scoring matrix state in an edit consisting only of multiple substitutes.
        """
        expected = numpy.array([[0,1,2,3,4,5],
                                [1,1,2,3,4,5],
                                [2,2,2,3,4,5],
                                [3,3,3,3,4,5],
                                [4,4,4,4,4,5],
                                [5,5,5,5,5,5]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('aaaaa', 'bbbbb')[0]))

    def test_all_insert(self):
        """
        Test the scoring matrix state in an edit consisting only of multiple inserts.
        """
        expected = numpy.array([[0,1,2,3,4,5]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('', 'abcde')[0]))        

    def test_all_delete(self):
        """
        Test the scoring matrix state in an edit consisting only of deletes.
        """
        expected = numpy.array([[0],
                                [1],
                                [2],
                                [3],
                                [4],
                                [5]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('abcde', '')[0]))

    def test_all_empty(self):
        """
        Test the scoring matrix state in an edit between two empty strings.
        """
        expected = numpy.zeros(shape=(1,1))
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('', '')[0]))

    # -------------------------------------------------------------------
    # Parameter tests ---------------------------------------------------
    # -------------------------------------------------------------------

    def test_substitution_parameter(self):
        """
        Test the functionality of the substitution score parameter.
        """
        default = algorithms.np_full_edit_distance('a', 'b')[0][-1,-1]
        same_as_default = algorithms.np_full_edit_distance('a', 'b', substitutionscore=1)[0][-1,-1]
        with_parameter = algorithms.np_full_edit_distance('a', 'b', substitutionscore=-7)[0][-1,-1]
        with_parameter_and_max = algorithms.np_full_edit_distance('a', 'b', substitutionscore=7)[0][-1,-1]
        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_deletion_parameter(self):
        """
        Test the functionality of the delete score parameter.
        """
        default = algorithms.np_full_edit_distance('a', '')[0][-1,-1]
        same_as_default = algorithms.np_full_edit_distance('a', '', deletescore=1)[0][-1,-1]
        with_parameter = algorithms.np_full_edit_distance('a', '', deletescore=-7)[0][-1,-1]

        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_insertion_parameter(self):
        """
        Test the functionality of the insert score parameter.
        """
        default = algorithms.np_full_edit_distance('', 'a')[0][-1,-1]
        same_as_default = algorithms.np_full_edit_distance('', 'a', insertscore=1)[0][-1,-1]
        with_parameter = algorithms.np_full_edit_distance('', 'a', insertscore=-7)[0][-1,-1]

        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_charmatrix_one_character_substitution_lower(self):
        """
        Test the functionality of the charmatrix parameter where in reduces the score of a substitution.
        """
        charmatrix = {('a', 'b'):0}
        expected = numpy.array([[0,1],
                                [1,0]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('a', 'b', charmatrix=charmatrix)[0]))

    def test_charmatrix_one_character_substitution_higher(self):
        """
        Test the functionality of the charmatrix parameter where in increases the score of a substitution.
        """
        charmatrix = {('a', 'b'):5}
        expected = numpy.array([[0,1],
                                [1,5]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('a', 'b', charmatrix=charmatrix)[0]))

    def test_charmatrix_one_character_substitution_default(self):
        """
        Test the functionality of the charmatrix parameter where it does not change a character score.
        """
        charmatrix = {('a', 'b'):1}
        expected = numpy.array([[0,1],
                                [1,1]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('a', 'b', charmatrix=charmatrix)[0]))


    def test_charmatrix_default_delete(self):
        """
        Test the case where the charmatrix mutates the score of trivial (first column) deletes.
        """
        charmatrix = {('', 'a'):5}
        expected = numpy.array([[0],
                                [5],
                                [10],
                                [15]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('aaa', '', charmatrix=charmatrix)[0]))

    def test_charmatrix_default_insert(self):
        """
        Test the case where the charmatrix mutates the score of trivial (first row) inserts.
        """
        charmatrix = {('a', ''):5}
        expected = numpy.array([[0,5,10,15]])
        self.assertTrue(numpy.array_equal(expected, algorithms.np_full_edit_distance('', 'aaa', charmatrix=charmatrix)[0]))

    # -------------------------------------------------------------------
    # Word tests --------------------------------------------------------
    # -------------------------------------------------------------------


    def test_identical_word(self):
        self.assertEqual(0, algorithms.np_full_edit_distance(['word'], ['word'])[0][-1,-1])
    
    def test_word_substitution(self):
        self.assertEqual(1, algorithms.np_full_edit_distance(['word'], ['different word'])[0][-1,-1])

    def test_word_insertion(self):
        self.assertEqual(1, algorithms.np_full_edit_distance([], ['word'])[0][-1,-1])

    def test_word_deletion(self):
        self.assertEqual(1, algorithms.np_full_edit_distance(['word'], [])[0][-1,-1])

    def test_word_multi_insert(self):
        self.assertEqual(5, algorithms.np_full_edit_distance([], ['word', 'word', 'word', 'word', 'word'])[0][-1,-1])

    def test_word_multi_delete(self):
        self.assertEqual(5, algorithms.np_full_edit_distance(['word', 'word', 'word', 'word', 'word'], [])[0][-1,-1])

    def test_word_multi_match(self):
        self.assertEqual(0, algorithms.np_full_edit_distance(['word1', 'word2', 'word3'], ['word1', 'word2', 'word3'])[0][-1,-1])

    def test_word_multi_substitute(self):
        self.assertEqual(3, algorithms.np_full_edit_distance(['word1', 'word2', 'word3'], ['otherword1', 'otherword2', 'otherword3'])[0][-1,-1])

class NumpyAlignmentTests(unittest.TestCase):

    def test_empty_strings(self):
        """
        Tests the edit steps between two empty strings.
        """
        self.assertEqual([], algorithms.np_align('', ''))
    
    def test_insertions(self):
        """
        Test the edit steps when only inserts are needed.
        """
        self.assertEqual(['i', 'i', 'i', 'i', 'i'], algorithms.np_align('', 'abcde'))

    def test_deletions(self):
        """
        Test the edit steps when only deletes are needed.
        """
        self.assertEqual(['d', 'd', 'd', 'd', 'd'], algorithms.np_align('abcde', ''))
        
    def test_matches(self):
        """
        Test the edit steps when only matches are needed.
        """
        self.assertEqual(['m', 'm', 'm', 'm', 'm'], algorithms.np_align('abcde', 'abcde'))

    def test_matches_1(self):   #TODO
        """
        Test the edit steps when only substitutions are needed.
        """
        self.assertEqual(['s', 's', 's', 's', 's'], algorithms.np_align('abcde', 'vwxyz'))

    def test_wikepedia_example_1(self):
        """
        Test against the first general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm
        """
        self.assertEqual(['s', 'm', 'm', 'm', 's', 'm', 'd'], algorithms.np_align('sitting', 'kitten'))

    def test_wikepedia_example_2(self):
        """
        Test against the second general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm
        """
        self.assertEqual(['m', 'i', 'i', 'm', 's', 'm', 'm', 'm'], algorithms.np_align('sunday', 'saturday'))


    # -------------------------------------------------------------------
    # Word Alignment Tests ----------------------------------------------
    # -------------------------------------------------------------------

    def test_empty_word_list(self):
        """
        Tests the edit steps between two empty lists.
        """
        self.assertEqual([], algorithms.np_align([], []))
    
    def test_word_insertions(self):
        """
        Test the edit steps when only inserts are needed.
        """
        self.assertEqual(['i', 'i', 'i', 'i', 'i'], algorithms.np_align([], ['word1', 'word2', 'word3', 'word4', 'word5']))

    def test_word_deletions(self):
        """
        Test the edit steps when only inserts are needed.
        """
        self.assertEqual(['d', 'd', 'd', 'd', 'd'], algorithms.np_align(['word1', 'word2', 'word3', 'word4', 'word5'], []))

    def test_word_matches(self):
        """
        Test the edit steps when only matches are needed.
        """
        self.assertEqual(['m', 'm', 'm', 'm', 'm'], algorithms.np_align(['word1', 'word2', 'word3', 'word4', 'word5'], ['word1', 'word2', 'word3', 'word4', 'word5']))

    def test_wikepedia_example_1(self):
        """
        Test against the first general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm, but as a list of words.
        """
        self.assertEqual(['s', 'm', 'm', 'm', 's', 'm', 'd'], algorithms.np_align(['s','i', 't', 't', 'i', 'n', 'g'], ['k','i', 't', 't', 'e', 'n']))

    def test_wikepedia_example_2(self):
        """
        Test against the second general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm, but as a list of words.
        """
        self.assertEqual(['m', 'i', 'i', 'm', 's', 'm', 'm', 'm'], algorithms.np_align(['s', 'u', 'n', 'd', 'a', 'y'], ['s','a', 't', 'u', 'r', 'd', 'a', 'y']))

class NumpySemiGlobalAlignmentTests(unittest.TestCase):
    """
    Tests the np_semi_global_align function.
    """

    def test_sequence_length_inversion(self):
        """
        Test that an exception is thrown if the first sequence is > the second.
        """
        self.assertRaises(algorithms.AlgorithmException, algorithms.np_semi_global_align, 'abcdefghi', '') #Test with a long string
        self.assertRaises(algorithms.AlgorithmException, algorithms.np_semi_global_align, 'a', '') # Test with one character
        self.assertRaises(algorithms.AlgorithmException, algorithms.np_semi_global_align, ['word'], []) # Test with one word
        self.assertRaises(algorithms.AlgorithmException, algorithms.np_semi_global_align, ['word1', 'word2', 'word3'], ['word']) # Test with one word

    def test_identical(self):
        """
        Test with strings and lists of equal length.
        """
        expected = ['m']
        self.assertEqual(expected, algorithms.np_semi_global_align('a', 'a'))
        self.assertEqual(expected, algorithms.np_semi_global_align(['a'], ['a']))

    def test_identical_long(self):
        """
        Test with a longer series of matches.
        """
        expected = ['m', 'm', 'm', 'm', 'm']
        self.assertEqual(expected, algorithms.np_semi_global_align('abcde', 'abcde'))

    def test_identical_words(self):
        """
        Test with a series of of matching words.
        """
        expected = ['m', 'm', 'm', 'm', 'm']
        self.assertEqual(expected, algorithms.np_semi_global_align(['word1', 'word2', 'word3', 'word4', 'word5'], ['word1', 'word2', 'word3', 'word4', 'word5']))

    def test_simple_prefix(self):
        """
        Test with a single match and a skippable prefix.
        """
        expected = ['i', 'i', 'i', 'i', 'm']
        self.assertEqual(expected, algorithms.np_semi_global_align('b', 'aaaab'))

    def test_prefix_with_trailer(self):
        """
        Test with a single match and a skippable prefix and trailer.
        """
        expected = ['i', 'i', 'i', 'i', 'm']
        self.assertEqual(expected, algorithms.np_semi_global_align('b', 'aaaabcccc'))

    def test_word_prefix(self):
        """
        Test a list of words with a prefix.
        """
        expected = ['i', 'i', 'm']
        self.assertEqual(expected, algorithms.np_semi_global_align(['match'], ['w1', 'w2', 'match']))

# ----------------------------------------------------------------------
# Language Tests -------------------------------------------------------
# ----------------------------------------------------------------------

class LanguageTests(unittest.TestCase):

    def test_unibarrier_arg_raise(self):
        """
        Tests that the proper exception is throw if an arg of type str
        is passed in.
        """
        @algorithms.unibarrier
        def dummyfunction(*args, **kwargs):
            pass

        self.assertRaises(algorithms.UnibarrierException, dummyfunction, 
                          str('a string'))

        self.assertRaises(algorithms.UnibarrierException, dummyfunction, 
                          str('a string'), str('another string'))

        self.assertRaises(algorithms.UnibarrierException, dummyfunction, 
                          str('100 of me!')*100, u'I donn\'t matter')

    def test_unibarrier_kwarg_raise(self):
        """
        Tests that the proper exception is throw if an kwarg of type str
        is passed in.
        """
        @algorithms.unibarrier
        def dummyfunction(*args, **kwargs):
            pass

        self.assertRaises(algorithms.UnibarrierException, dummyfunction, 
                          kw1=str('a string'))

        self.assertRaises(algorithms.UnibarrierException, dummyfunction, 
                          kw1=str('a string'), kw2=str('another string'))

        self.assertRaises(algorithms.UnibarrierException, dummyfunction, 
                          largekw=str('100 of me!')*100)

        self.assertRaises(algorithms.UnibarrierException, dummyfunction, 
                          largekw=str('100 of me!')*100, kw=u'I don\'t matter')

    def test_unibarrier_passthrough(self):
        """
        Test that args and kwargs of type unicode do not cause an
        exception to be raised.
        """
        @algorithms.unibarrier
        def dummyfunction(*args, **kwargs):
            pass

        try:
            dummyfunction()
            dummyfunction(u'a unicode arg')
            dummyfunction(u'a unicode arg', u'another uni arg')
            dummyfunction(kw1=u'a unicode kwarg')
            dummyfunction(kw1=u'a unicode kwarg', kw2=u'another unicode kwarg')
            dummyfunction(u'a unicode arg', u'another uni arg',
                          kw1=u'a unicode kwarg', kw2=u'another unicode kwarg')
        except UnibarrierException, e:
            self.fail()

    def test_inblock(self):
        """
        Tests the inblock function using the printable part of the ascii
        block. This block was chosen arbitrarily.
        """
        asciistr = (u"""!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUV"""
                       """WXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~""")
        for c in asciistr:
            self.assertTrue(algorithms.inblock(c, ('!', '~')))

        self.assertFalse(algorithms.inblock(unichr(ord('!')-1), ('!', '~')))
        self.assertFalse(algorithms.inblock(unichr(ord('~')+1), ('!', '~')))

    def test_identify_all_ascii_simple(self):
        """
        Test the text identify method against the ascii unicode block.
        """
        asciistr = (u'ascii', unichr(0), unichr(127))
        ex1 = algorithms.identify(u'this is a string of ascii', [asciistr])
        self.assertEqual(ex1, {u'ascii':25})

    def test_identify_all_ascii(self):
        """
        Test the text identify method against the ascii unicode block.
        """
        asciistr = (u'ascii', unichr(0), unichr(127))

        for i in xrange(0, 128):
            self.assertEqual({u'ascii': 1}, algorithms.identify(unichr(i), [asciistr]))

    def test_identify_greek_and_latin(self):
        """
        Test the identify method on a string that contains both greek
        and latin characters.
        """
        ascii = (u'ascii', unichr(0), unichr(127))
        greek = (u'Greek Coptic', u'\u0370', u'\u03FF')

        self.assertEqual({greek[0]:len(u'Σωκράτης')},
                         algorithms.identify(u'Σωκράτης', [greek]))
        self.assertEqual({greek[0]:len(u'Πλάτων')},
                         algorithms.identify(u'Πλάτων', [greek]))

# ----------------------------------------------------------------------
# Word Alignment Tests -------------------------------------------------
# ----------------------------------------------------------------------

class HocrTests(unittest.TestCase):
    """
    Tests algorithms dealing with hocr manipulation.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryFile()

    def tearDown(self):
        self.temp.close()
        

    def test_simple_word_extract(self):
        self.temp.write("""<html><body><span class='ocrx_word' id='word_10' title="bbox 260 196 305 232">εἰς</span></body><html>""")
        self.temp.seek(0,0)
        for t in algorithms.extract_hocr_tokens(self.temp):
            self.assertEqual('εἰς'.decode('utf-8'), t)

    def test_bbox_extract_simple(self):
        """"
        Test hocr bbox extraction in some simple cases.
        """
        self.temp.write(u'<root title="bbox 1 2 3 4"></root>')
        self.temp.seek(0,0)
        bboxes = algorithms.extract_bboxes(self.temp)
        self.assertEqual([(1, 2, 3, 4)], bboxes)

    def test_bbox_extract_complex(self):
        """
        Test hocr bbox extraction on a larger document which exercises 
        the bbox identifying regex.
        """
        self.temp.write(u"""<root>"""
                         """<p title="text before bbox 1 2 3 4"></p>"""
                         """<p title="bbox 5 6 7 8textafter"></p>"""
                         """<p title="textbeforebbox 9 10 11 12textafter"></p>"""
                         """</root>""")
        self.temp.seek(0,0)

        bboxes = algorithms.extract_bboxes(self.temp)
        self.assertEqual((1, 2, 3, 4), bboxes[0])
        self.assertEqual((5, 6, 7, 8), bboxes[1])
        self.assertEqual((9, 10, 11, 12), bboxes[2])


if __name__ == '__main__':
    unittest.main()
