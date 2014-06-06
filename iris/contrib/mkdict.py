#! /usr/bin/env python
# -*- coding: utf-8 -*-

from algorithms import strings_by_deletion,sanitize 
import sys
import cPickle
from time import sleep

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('mkdict [word list] [dictionary file]')
        exit()
    print(u'Reading word list from ' + sys.argv[1].decode(sys.stdin.encoding))
    with open(sys.argv[1]) as word_list:
        dic = {}
        for w in word_list:
            w = sanitize(w)
            if w not in dic:
                dic[w] = set()
            dic[w].union(set(strings_by_deletion(w, 2)))
        with open(sys.argv[2], 'wb') as out_file:
            print(u'Writing to ' + sys.argv[2].decode(sys.stdin.encoding))
            cPickle.dump(dic, out_file)
