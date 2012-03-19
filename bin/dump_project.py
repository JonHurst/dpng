#!/usr/bin/python

import pickle
import sys


project = open(sys.argv[1])
meta, project_data = pickle.load(project)
print "Title:", meta["title"]
print "Project ID:", meta["id"]
print "\nPages:\n"
for e in sorted(project_data):
    print e, project_data[e], "\n"
