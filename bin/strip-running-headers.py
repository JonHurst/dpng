#!/usr/bin/python

import pickle
import sys

meta, data = pickle.load(open(sys.argv[1]))
for page in data:
    print "before"
    print data[page][1]
    if len(data[page][1]):
        del data[page][1][0]
    print "after"
    print data[page][1]
if raw_input("Continue (y|n)?\n") == "y":
    pickle.dump((meta, data), open(sys.argv[1], "w"))

