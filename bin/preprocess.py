#!/usr/bin/python
# coding=utf-8

import project_data
import re
import sys

pd = project_data.ProjectData(sys.argv[1], True)
pages = pd.get_pages()
for p in pages:
    if pd.exists(p[0], "preproof"): continue
    text, timestamp, status = pd.get_text(p[0], "ocr")
    print p[0]
    text = text.replace("ﬁ", "fi")
    text = text.replace("ﬀ", "ff")
    text = text.replace("ﬂ", "fl")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"‘\s*", "'", text)
    text = re.sub(r"\s*’", "'", text)
    text = re.sub(r"“\s*", '"', text)
    text = re.sub(r"\s*”", '"', text)
    text = text.replace("`", "'")
    text = text.replace("—", "--")
    text = text.replace("]", "J")
    text = text.replace("·", "")
    text = text.replace("VV", "W")
    text = text.replace("\V", "W")
    text = re.sub(r" *--+ *", "--", text)
    text = re.sub(r"\s*([\;\:\!\?\,])", r"\1", text)
    text = re.sub(r"(\n[\'\"])\s*", r"\1", text)
    text = re.sub(r"\s*([\'\"]\n)", r"\1", text)
    pd.set_text(p[0], text, "ocr", False)
pd.save()
pd.unlock()

