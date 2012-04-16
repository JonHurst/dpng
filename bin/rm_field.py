#!/usr/bin/python
# coding=utf-8

import project_data
import re
import sys

if len(sys.argv) != 3:
    print "Usage: ", sys.argv[0], "PROJECT_FILE", "FIELD"
pd = project_data.ProjectData(sys.argv[1], True)
for pid, ts, s in pd.get_pages():
    pd.rm_data(pid, sys.argv[2])
pd.save()
