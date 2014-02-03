# -*- coding: utf-8 -*-
import unittest
import algorithms

class LevenshteinTests(unittest.TestCase):

    def test_equal_strings(self):
        self.assertEqual(0, algorithms.edit_distance('test_string', 'test_string'))

    def test_single_insert(self):
        self.assertEqual(1, algorithms.edit_distance('', 'a'))

    def test_tenfold_insert(self):
        self.assertEqual(10, algorithms.edit_distance('', 'aaaaaaaaaa')) # A string with 10 a's.

    def test_single_delete(self):
        self.assertEqual(1, algorithms.edit_distance('a', ''))

    def test_tenfold_delete(self):
        self.assertEqual(10, algorithms.edit_distance('aaaaaaaaaa', '')) # A string with 10 a's.

    def test_singledelete_singleadd(self):
        self.assertEqual(2, algorithms.edit_distance('abbb', 'bbbbb')) # Should delete the a and add the final b.

    def test_singleadd_singledelete(self):
        self.assertEqual(2, algorithms.edit_distance('bbbbb', 'abbb')) # Should delete the a and add the final b.

if __name__ == '__main__':
    unittest.main()