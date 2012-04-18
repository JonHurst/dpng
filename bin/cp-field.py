#!/usr/bin/python
# coding=utf-8

import project_data
import re
import sys

if len(sys.argv) != 4:
    print "Usage: ", sys.argv[0], "PROJECT_FILE", "FROM_FIELD", "TO_FIELD"
pd = project_data.ProjectData(sys.argv[1], True)
for pageid in pd.project_data.keys():
    if pd.project_data[pageid].has_key(sys.argv[2]):
        pd.project_data[pageid][sys.argv[3]] = pd.project_data[pageid][sys.argv[2]]
pd.save()
