#!/usr/bin/python

import sys
import command

current_project = "/home/jon/public_html/data/projectID4ed1b63667527/project"
d = command.ProjectData(current_project)
pageid = open(sys.argv[1]).read(3)
text = d.get_text(pageid, "127.0.0.1")
open(sys.argv[1], "w").write(text.encode("utf-8"))
