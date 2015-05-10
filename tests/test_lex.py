# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import shutil

from mock import patch, MagicMock


class DictTests(unittest.TestCase):

    """
    General tests for the dict.py module.
    """

    def setUp(self):
        # Make a temp sample dictionary
        self.temp = tempfile.NamedTemporaryFile()
        self.temp.write(u'word1\n'.encode(u'utf-8'))
        self.temp.write(u'word2\n'.encode(u'utf-8'))
        self.temp.write(u'αχιλλεύς\n'.encode(u'utf-8'))  # Achilles, in NFD
        self.temp.write(u'αχιλλεύς\n'.encode(u'utf-8'))  # Achilles, in NFC
        self.temp.seek(0, 0)
        self.path = os.path.abspath(self.temp.name).decode(u'utf-8')

        # Make an empty temp directory for general use
        self.tempdir = tempfile.mkdtemp().decode('utf-8')
        
        self.config_mock = MagicMock()
        self.config_mock.nidaba.config.everything.log.return_value = True
        modules = {
            'nidaba.config': self.config_mock.config
        }
        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        from nidaba import lex
        self.lex = lex

    def tearDown(self):
        self.temp.close()
        shutil.rmtree(self.tempdir)

    def test_cleanlines(self):
        """
        Test the cleanline function.
        """
        words = self.lex.cleanlines(self.path)
        self.assertEqual(len(words), 4)
        self.assertEqual(words[0], u'word1')
        self.assertEqual(words[1], u'word2')
        self.assertEqual(words[2], u'αχιλλεύς')
        self.assertEqual(words[3], u'αχιλλεύς')

    def test_cleanwords(self):
        """
        Test the cleanwords function.
        """
        self.temp.write(
            u'adding a line with multiple words\n'.encode(u'utf-8'))
        self.temp.write(u'another with Greek αχιλλεύς\n'.encode(u'utf-8'))
        self.temp.write(u'and some NFC αχιλλεύς\n'.encode(u'utf-8'))
        self.temp.seek(0, 0)
        expected = [u'adding', u'a', u'line', u'with', u'multiple', u'words',
                    u'another', u'with', u'Greek', u'αχιλλεύς', u'and',
                    u'some', u'NFC', u'αχιλλεύς']
        words = self.lex.cleanwords(self.path)
        self.assertEqual(words, expected)

    def test_cleanuniquewords(self):
        """
        Test the cleanuniquewords function.
        """
        self.temp1 = tempfile.NamedTemporaryFile()
        self.temp1.write(
            u'adding a line with multiple words\n'.encode(u'utf-8'))
        self.temp1.write(u'another with Greek αχιλλεύς\n'.encode(u'utf-8'))
        self.temp1.write(u'and some NFC αχιλλεύς\n'.encode(u'utf-8'))
        self.temp1.seek(0, 0)
        expected = set([u'adding', u'a', u'line', u'with', u'multiple',
                        u'words', u'another', u'with', u'Greek', u'αχιλλεύς',
                        u'and', u'some', u'NFC', u'αχιλλεύς'])
        self.assertEqual(
            self.lex.cleanuniquewords(self.temp1.name.decode(u'utf-8')), expected)

    def test_words_from_files(self):
        """
        Test the words_from_files function.
        """
        self.temp1 = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=True)
        self.temp2 = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=True)
        self.temp3 = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=True)
        self.dirtofilter = tempfile.mkdtemp(
            dir=self.tempdir)  # To be filtered out
        self.temp1.write(u'a')
        self.temp2.write(u'b')
        self.temp3.write(u'c')
        self.temp1.seek(0, 0)
        self.temp2.seek(0, 0)
        self.temp3.seek(0, 0)
        words = self.lex.words_from_files(self.tempdir)
        self.assertEqual(3, len(words))
        self.assertTrue(u'a' in words)
        self.assertTrue(u'b' in words)
        self.assertTrue(u'c' in words)
        self.temp1.close()
        self.temp2.close()
        self.temp3.close()

    def test_unique_words_from_files(self):
        """
        Test the words_from_files_function.
        """
        self.temp1 = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=True)
        self.temp2 = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=True)
        self.temp3 = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=True)
        self.temp4 = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=True)
        self.dirtofilter = tempfile.mkdtemp(
            dir=self.tempdir)  # To be filtered out
        self.temp1.write(u'a')
        self.temp2.write(u'b b')
        self.temp3.write(u'c a')
        self.temp4.write(u'a b c \nd')
        self.temp1.seek(0, 0)
        self.temp2.seek(0, 0)
        self.temp3.seek(0, 0)
        self.temp4.seek(0, 0)
        words = self.lex.unique_words_from_files(self.tempdir)
        self.assertEqual(4, len(words))
        self.assertTrue(u'a' in words)
        self.assertTrue(u'b' in words)
        self.assertTrue(u'c' in words)
        self.assertTrue(u'd' in words)
        self.temp1.close()
        self.temp2.close()
        self.temp3.close()
        self.temp4.close()

    def test_make_dict(self):
        """
        Test the make_dict function.
        """
        words = [u'a', u'b', u'c', u'd']
        mytemp = tempfile.mkdtemp().decode('utf-8')
        outpath = os.path.join(mytemp, u'testdict')
        self.lex.make_dict(outpath, words)
        retrived = self.lex.cleanuniquewords(outpath)
        self.assertEqual(len(retrived), 4)
        self.assertTrue(u'a' in retrived)
        self.assertTrue(u'b' in retrived)
        self.assertTrue(u'c' in retrived)
        self.assertTrue(u'd' in retrived)
        shutil.rmtree(mytemp)

    def test_make_deldict_1(self):
        """
        Test the make_deldict function at depth 1.
        """
        outfile = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=True)
        words = [u'aaa', u'bbb', u'ccc', u'ddd']
        self.lex.make_deldict(outfile.name, words, 1)
        lines = self.lex.cleanlines(outfile.name)
        self.assertEqual(u'aa\taaa', lines[0])
        self.assertEqual(u'bb\tbbb', lines[1])
        self.assertEqual(u'cc\tccc', lines[2])
        self.assertEqual(u'dd\tddd', lines[3])
        outfile.close()

    def test_unique_words_with_frequency(self):
        """
        Test the uniquewords_with_freq function
        """
        temp = tempfile.NamedTemporaryFile()
        temp.write('a a a a b b c c c b b b b d \n foobar foobar')
        temp.seek(0, 0)
        f = self.lex.uniquewords_with_freq(temp.name.decode('utf-8'))
        self.assertEqual(5, len(f.keys()))
        self.assertEqual(4, f['a'])
        self.assertEqual(6, f['b'])
        self.assertEqual(3, f['c'])
        self.assertEqual(1, f['d'])
        self.assertEqual(2, f['foobar'])

if __name__ == '__main__':
    unittest.main()
