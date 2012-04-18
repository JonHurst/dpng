#!/usr/bin/python
# coding=utf-8

import project_data
import re
import sys
import hashlib
import glob
import os

if len(sys.argv) != 2:
    print "Usage: ", sys.argv[0], "PROJECT_FILE"
name_length  = len(hashlib.sha1("").hexdigest())
proj_directory = os.path.dirname(os.path.abspath(sys.argv[1]))
#build set of candidate files
all_files = [os.path.basename(X)
             for X in glob.glob(os.path.join(proj_directory, "*"))]
all_files = set([X for X in all_files if len(X) == name_length])
#build an "in use" list
in_use = set()
pd = project_data.ProjectData(sys.argv[1])
for pageid in pd.project_data.keys():
    for field in pd.project_data[pageid].keys():
        if field not in ("lines", "images"):
            in_use.add(pd.project_data[pageid][field][0])
to_unlink = all_files - in_use
for f in to_unlink:
    f = os.path.join(proj_directory, f)
    print "unlinking", f
    os.unlink(f)

