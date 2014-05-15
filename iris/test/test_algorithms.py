#! /usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import algorithms
import numpy

class OptimizedLevenshteinTests(unittest.TestCase):
    """Tests the optimized edit distance algorithm by checking the resultant edit distance, but not the internal matrix, as this is not stored.
    Tests are identical to those for the full Levenshtein tests where applicable."""

    def test_equal_strings(self):
        """Test the edit distance of identical strings"""
        self.assertEqual(0, algorithms.edit_distance('test_string', 'test_string'))

    def test_single_insert(self):
        """Test with strings requiring one insert"""
        self.assertEqual(1, algorithms.edit_distance('', 'a'))

    def test_tenfold_insert(self):
        """Test with strings requiring ten inserts"""
        self.assertEqual(10, algorithms.edit_distance('', 'aaaaaaaaaa')) # A string with 10 a's.

    def test_single_delete(self):
        """Test with strings requiring one delete"""
        self.assertEqual(1, algorithms.edit_distance('a', ''))

    def test_tenfold_delete(self):
        """Test with strings requiring ten deletes"""
        self.assertEqual(10, algorithms.edit_distance('aaaaaaaaaa', '')) # A string with 10 a's.

    def test_singledelete_singleadd(self):
        """Test with strings requiring a single non-trivial insert."""
        self.assertEqual(2, algorithms.edit_distance('abbb', 'bbbbb')) # Should delete the a and insert the final b.

    def test_singleadd_singledelete(self):
        """Test with strings requiring a single non-trivial delete."""
        self.assertEqual(2, algorithms.edit_distance('bbbbb', 'abbb')) # Should delete the a and add the final b.

class LevenshteinTests(unittest.TestCase):
    """Tests the full_edit_distance funtion by checking both the edit distance and full matrix comparisons."""

    # -------------------------------------------------------------------
    # Edit distance tests -----------------------------------------------
    # -------------------------------------------------------------------

    def test_equal_strings(self):
        """Test the edit distance of identical strings"""
        self.assertEqual(0, algorithms.full_edit_distance('test_string', 'test_string')[0][-1,-1])

    def test_single_insert(self):
        """Test with strings requiring one insert"""
        self.assertEqual(1, algorithms.full_edit_distance('', 'a')[0][-1,-1])

    def test_tenfold_insert(self):
        """Test with strings requiring ten inserts"""
        self.assertEqual(10, algorithms.full_edit_distance('', 'aaaaaaaaaa')[0][-1,-1]) # A string with 10 a's.

    def test_single_delete(self):
        """Test with strings requiring one delete"""
        self.assertEqual(1, algorithms.full_edit_distance('a', '')[0][-1,-1])

    def test_tenfold_delete(self):
        """Test with strings requiring ten deletes"""
        self.assertEqual(10, algorithms.full_edit_distance('aaaaaaaaaa', '')[0][-1,-1]) # A string with 10 a's.

    def test_singledelete_singleadd(self):
        """Test with strings requiring a single non-trivial insert."""
        self.assertEqual(2, algorithms.full_edit_distance('abbb', 'bbbbb')[0][-1,-1]) # Should delete the a and insert the final b.

    def test_singleadd_singledelete(self):
        """Test with strings requiring a single non-trivial delete."""
        self.assertEqual(2, algorithms.full_edit_distance('bbbbb', 'abbb')[0][-1,-1]) # Should delete the a and add the final b.    

    # -------------------------------------------------------------------
    # Score matrix tests ------------------------------------------------
    # -------------------------------------------------------------------

    def test_match_delete_matrix(self):
        """Test the scoring matrix state in an edit requiring one match and delete."""
        expected = numpy.array([[0,1,2],[1,0,1]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('a', 'ab')[0]))

    def test_match_insert_matrix(self):
        """Test the scoring matrix state in an edit requiring one match an insert."""
        expected = numpy.array([[0,1],[1,0],[2,1]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('ab', 'a')[0]))

    def test_all_match_matrix(self):
        """Test the scoring matrix state in an edit consisting only of multiple matches."""
        expected = numpy.array([[0,1,2,3,4,5],
                                [1,0,1,2,3,4],
                                [2,1,0,1,2,3],
                                [3,2,1,0,1,2],
                                [4,3,2,1,0,1],
                                [5,4,3,2,1,0]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('aaaaa', 'aaaaa')[0]))


    def test_all_subtitute_matrix(self):
        """Test the scoring matrix state in an edit consisting only of multiple substitutes."""
        expected = numpy.array([[0,1,2,3,4,5],
                                [1,1,2,3,4,5],
                                [2,2,2,3,4,5],
                                [3,3,3,3,4,5],
                                [4,4,4,4,4,5],
                                [5,5,5,5,5,5]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('aaaaa', 'bbbbb')[0]))

    def test_all_insert(self):
        """Test the scoring matrix state in an edit consisting only of multiple inserts."""
        expected = numpy.array([[0,1,2,3,4,5]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('', 'abcde')[0]))        

    def test_all_delete(self):
        """Test the scoring matrix state in an edit consisting only of deletes."""
        expected = numpy.array([[0],
                                [1],
                                [2],
                                [3],
                                [4],
                                [5]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('abcde', '')[0]))

    def test_all_empty(self):
        """Test the scoring matrix state in an edit between two empty strings."""
        expected = numpy.zeros(shape=(1,1))
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('', '')[0]))

    # -------------------------------------------------------------------
    # Parameter tests ---------------------------------------------------
    # -------------------------------------------------------------------

    def test_substitution_parameter(self):
        """Test the functionality of the substitution score parameter."""
        default = algorithms.full_edit_distance('a', 'b')[0][-1,-1]
        same_as_default = algorithms.full_edit_distance('a', 'b', substitutionscore=1)[0][-1,-1]
        with_parameter = algorithms.full_edit_distance('a', 'b', substitutionscore=-7)[0][-1,-1]
        with_parameter_and_max = algorithms.full_edit_distance('a', 'b', substitutionscore=7)[0][-1,-1]
        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_deletion_parameter(self):
        """Test the functionality of the delete score parameter."""
        default = algorithms.full_edit_distance('a', '')[0][-1,-1]
        same_as_default = algorithms.full_edit_distance('a', '', deletescore=1)[0][-1,-1]
        with_parameter = algorithms.full_edit_distance('a', '', deletescore=-7)[0][-1,-1]

        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_insertion_parameter(self):
        """Test the functionality of the insert score parameter."""
        default = algorithms.full_edit_distance('', 'a')[0][-1,-1]
        same_as_default = algorithms.full_edit_distance('', 'a', insertscore=1)[0][-1,-1]
        with_parameter = algorithms.full_edit_distance('', 'a', insertscore=-7)[0][-1,-1]

        self.assertEqual(1, default)
        self.assertEqual(1, same_as_default)
        self.assertEqual(-7, with_parameter)

    def test_charmatrix_one_character_substitution_lower(self):
        """Test the functionality of the charmatrix parameter where in reduces the score of a substitution."""
        charmatrix = {('a', 'b'):0}
        expected = numpy.array([[0,1],
                                [1,0]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('a', 'b', charmatrix=charmatrix)[0]))

    def test_charmatrix_one_character_substitution_higher(self):
        """Test the functionality of the charmatrix parameter where in increases the score of a substitution."""
        charmatrix = {('a', 'b'):5}
        expected = numpy.array([[0,1],
                                [1,5]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('a', 'b', charmatrix=charmatrix)[0]))

    def test_charmatrix_one_character_substitution_default(self):
        """Test the functionality of the charmatrix parameter where it does not change a character score."""
        charmatrix = {('a', 'b'):1}
        expected = numpy.array([[0,1],
                                [1,1]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('a', 'b', charmatrix=charmatrix)[0]))


    def test_charmatrix_default_delete(self):
        """Test the case where the charmatrix mutates the score of trivial (first column) deletes."""
        charmatrix = {('', 'a'):5}
        expected = numpy.array([[0],
                                [5],
                                [10],
                                [15]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('aaa', '', charmatrix=charmatrix)[0]))

    def test_charmatrix_default_insert(self):
        """Test the case where the charmatrix mutates the score of trivial (first row) inserts."""
        charmatrix = {('a', ''):5}
        expected = numpy.array([[0,5,10,15]])
        self.assertTrue(numpy.array_equal(expected, algorithms.full_edit_distance('', 'aaa', charmatrix=charmatrix)[0]))

    # -------------------------------------------------------------------
    # Word tests --------------------------------------------------------
    # -------------------------------------------------------------------


    def test_identical_word(self):
        self.assertEqual(0, algorithms.full_edit_distance(['word'], ['word'])[0][-1,-1])
    
    def test_word_substitution(self):
        self.assertEqual(1, algorithms.full_edit_distance(['word'], ['different word'])[0][-1,-1])

    def test_word_insertion(self):
        self.assertEqual(1, algorithms.full_edit_distance([], ['word'])[0][-1,-1])

    def test_word_deletion(self):
        self.assertEqual(1, algorithms.full_edit_distance(['word'], [])[0][-1,-1])

    def test_word_multi_insert(self):
        self.assertEqual(5, algorithms.full_edit_distance([], ['word', 'word', 'word', 'word', 'word'])[0][-1,-1])

    def test_word_multi_delete(self):
        self.assertEqual(5, algorithms.full_edit_distance(['word', 'word', 'word', 'word', 'word'], [])[0][-1,-1])

    def test_word_multi_match(self):
        self.assertEqual(0, algorithms.full_edit_distance(['word1', 'word2', 'word3'], ['word1', 'word2', 'word3'])[0][-1,-1])

    def test_word_multi_substitute(self):
        self.assertEqual(3, algorithms.full_edit_distance(['word1', 'word2', 'word3'], ['otherword1', 'otherword2', 'otherword3'])[0][-1,-1])

class AlignmentTests(unittest.TestCase):

    def test_empty_strings(self):
        """Tests the edit steps between two empty strings."""
        self.assertEqual([], algorithms.align('', ''))
    
    def test_insertions(self):
        """Test the edit steps when only inserts are needed."""
        self.assertEqual(['i', 'i', 'i', 'i', 'i'], algorithms.align('', 'abcde'))

    def test_deletions(self):
        """Test the edit steps when only deletes are needed."""
        self.assertEqual(['d', 'd', 'd', 'd', 'd'], algorithms.align('abcde', ''))
        
    def test_matches(self):
        """Test the edit steps when only matches are needed."""
        self.assertEqual(['m', 'm', 'm', 'm', 'm'], algorithms.align('abcde', 'abcde'))

    def test_matches_1(self):   #TODO
        """Test the edit steps when only substitutions are needed."""
        self.assertEqual(['s', 's', 's', 's', 's'], algorithms.align('abcde', 'vwxyz'))

    def test_wikepedia_example_1(self):
        """Test against the first general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm"""
        self.assertEqual(['s', 'm', 'm', 'm', 's', 'm', 'd'], algorithms.align('sitting', 'kitten'))

    def test_wikepedia_example_2(self):
        """Test against the second general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm"""
        self.assertEqual(['m', 'i', 'i', 'm', 's', 'm', 'm', 'm'], algorithms.align('sunday', 'saturday'))


    # -------------------------------------------------------------------
    # Word Alignment Tests ----------------------------------------------
    # -------------------------------------------------------------------

    def test_empty_word_list(self):
        """Tests the edit steps between two empty lists."""
        self.assertEqual([], algorithms.align([], []))
    
    def test_word_insertions(self):
        """Test the edit steps when only inserts are needed."""
        self.assertEqual(['i', 'i', 'i', 'i', 'i'], algorithms.align([], ['word1', 'word2', 'word3', 'word4', 'word5']))

    def test_word_deletions(self):
        """Test the edit steps when only inserts are needed."""
        self.assertEqual(['d', 'd', 'd', 'd', 'd'], algorithms.align(['word1', 'word2', 'word3', 'word4', 'word5'], []))

    def test_word_matches(self):
        """Test the edit steps when only matches are needed."""
        self.assertEqual(['m', 'm', 'm', 'm', 'm'], algorithms.align(['word1', 'word2', 'word3', 'word4', 'word5'], ['word1', 'word2', 'word3', 'word4', 'word5']))

    def test_wikepedia_example_1(self):
        """Test against the first general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm, but as a list of words."""
        self.assertEqual(['s', 'm', 'm', 'm', 's', 'm', 'd'], algorithms.align(['s','i', 't', 't', 'i', 'n', 'g'], ['k','i', 't', 't', 'e', 'n']))

    def test_wikepedia_example_2(self):
        """Test against the second general example provided at http://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm, but as a list of words."""
        self.assertEqual(['m', 'i', 'i', 'm', 's', 'm', 'm', 'm'], algorithms.align(['s', 'u', 'n', 'd', 'a', 'y'], ['s','a', 't', 'u', 'r', 'd', 'a', 'y']))

class SemiGlobalAlignmentTests(unittest.TestCase):
    """Tests the semi_global_align function."""

    def test_sequence_length_inversion(self):
        """Test that an exception is thrown if the first sequence is > the second."""
        self.assertRaises(algorithms.AlgorithmException, algorithms.semi_global_align, 'abcdefghi', '') #Test with a long string
        self.assertRaises(algorithms.AlgorithmException, algorithms.semi_global_align, 'a', '') # Test with one character
        self.assertRaises(algorithms.AlgorithmException, algorithms.semi_global_align, ['word'], []) # Test with one word
        self.assertRaises(algorithms.AlgorithmException, algorithms.semi_global_align, ['word1', 'word2', 'word3'], ['word']) # Test with one word

    def test_identical(self):
        """Test with strings and lists of equal length."""
        expected = ['m']
        self.assertEqual(expected, algorithms.semi_global_align('a', 'a'))
        self.assertEqual(expected, algorithms.semi_global_align(['a'], ['a']))

    def test_identical_long(self):
        """Test with a longer series of matches."""
        expected = ['m', 'm', 'm', 'm', 'm']
        self.assertEqual(expected, algorithms.semi_global_align('abcde', 'abcde'))

    def test_identical_words(self):
        """Test with a series of of matching words."""
        expected = ['m', 'm', 'm', 'm', 'm']
        self.assertEqual(expected, algorithms.semi_global_align(['word1', 'word2', 'word3', 'word4', 'word5'], ['word1', 'word2', 'word3', 'word4', 'word5']))

    def test_simple_prefix(self):
        """Test with a single match and a skippable prefix."""
        expected = ['i', 'i', 'i', 'i', 'm']
        self.assertEqual(expected, algorithms.semi_global_align('b', 'aaaab'))

    def test_prefix_with_trailer(self):
        """Test with a single match and a skippable prefix and trailer."""
        expected = ['i', 'i', 'i', 'i', 'm']
        self.assertEqual(expected, algorithms.semi_global_align('b', 'aaaabcccc'))

    def test_word_prefix(self):
        """Test a list of words with a prefix."""
        expected = ['i', 'i', 'm']
        self.assertEqual(expected, algorithms.semi_global_align(['match'], ['w1', 'w2', 'match']))


if __name__ == '__main__':
    unittest.main()
