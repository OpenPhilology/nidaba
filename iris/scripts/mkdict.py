#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import codecs
import cPickle
from time import sleep
from algorithms import strings_by_deletion,sanitize 


def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

if __name__ == '__main__':
    """
    Generate a dictionary for symmetric deletion spell checking.
    Lines in the dictionary are of the form:
    variant : [list of originals]
    """
    if len(sys.argv) != 4:
        print u'mkdict [word list] [dictionary file] [edit distance]'
        exit()
    elif sys.argv[3] <= 0:
        print 'Error depth must be positive'
    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    edit_distance = int(sys.argv[3])
    
    fl = file_len(input_file_path)

    with open(input_file_path) as infile:
        i = 0
        dic = {}
        for word in infile:
            word = sanitize(word)
            variants = strings_by_deletion(word, edit_distance)
            i += 1
            sys.stdout.write("Words generated:%d/%i   \r" % (i, fl) )
            sys.stdout.flush()

            for v in variants:
                if v not in dic:
                    dic[v] = []
                dic[v].append(word)

    print 'sorting...'
    ordered = dic.keys()
    ordered.sort()

    print '\n'
    print 'writing file' 
    with codecs.open(output_file_path, u'w+', encoding='utf-8') as outfile:
        i = 0
        for k in ordered:
            sys.stdout.write("Entries written:%d/%i   \r" % (i, len(dic)-1) )
            if i != fl - 1:
                sys.stdout.flush()

            originals = u' '.join(dic[k])
            outfile.write(u'%s : %s' % (k, originals) + u'\n')
            i += 1
    print '\n'