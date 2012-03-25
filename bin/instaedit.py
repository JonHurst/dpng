#!/usr/bin/python

import sys
import project_data

current_project = "/home/jon/public_html/data/projectID4f680ded3a815/project"
d = project_data.ProjectData(current_project)
pageid = open(sys.argv[1]).read(3)
text = unicode(d.get_text(pageid, "127.0.0.1")[0], "utf-8")
open(sys.argv[1], "w").write(text.encode("utf-8"))
