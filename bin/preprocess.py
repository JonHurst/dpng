#!/usr/bin/python
# coding=utf-8

import project_data
import re
import sys

pd = project_data.ProjectData(sys.argv[1], True)
pages = pd.get_pages()
for p in pages:
    print p[0]
    if int(p[0]) < 57: continue
    text, timestamp, status = pd.get_text(p[0], "127.0.0.1")
    text = re.sub(r"‘\s*", "'", text)
    text = re.sub(r"\s*’", "'", text)
    text = text.replace("`", "'")
    text = text.replace("—", "-")
    text = text.replace("]", "J")
    text = text.replace("·", "")
    text = re.sub(r"\s*([\;\:\!\?\,])", r"\1", text)
    text = re.sub(r"(\n[\'\"])\s*", r"\1", text)
    text = re.sub(r"\s*([\'\"]\n)", r"\1", text)
    pd.set_text(p[0], text, "127.0.0.1", False)
pd.save()
pd.unlock()

