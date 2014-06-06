#! /usr/bin/env python
# -*- coding: utf-8 -*-

from algorithms import strings_by_deletion,sanitize 
import sys
import cPickle
from time import sleep

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('mkdict [word list] [dictionary file] [edit distance]')
        exit()
    print(u'Reading word list from ' + sys.argv[1].decode(sys.stdin.encoding))
    ed = int(sys.argv[3])
    lines = file_len(sys.argv[1])
    with open(sys.argv[1]) as word_list:
        dic = {}
        j = 0
        for candidate in word_list:
            candidate = sanitize(candidate)
            sys.stdout.write('\r' + str(j) + '/' + str(lines))
            sys.stdout.flush()
            j = j + 1
            # we add terms of edit distance 0 to the dictionary so we can
            # determine correctly spelled words by checking if term occurs in
            # the associated list of candidates.
            for i in xrange(0, ed+1):
                for term in strings_by_deletion(candidate, i):
                    if term not in dic:
                        dic[term] = set()
                    dic[term].add((candidate, i))
        with open(sys.argv[2], 'wb') as out_file:
            print(u'Writing to ' + sys.argv[2].decode(sys.stdin.encoding))
            cPickle.dump({u'edit_distance': ed, u'dictionary': dic}, out_file)
