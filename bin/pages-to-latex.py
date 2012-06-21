#!/usr/bin/python

import sys
import os
import re
import project_data

latex_escape_table = [
    ("\\", r"\textbackslash"),
    ("--", " --- "),
    ("---  ---", "------"),
    ("$", r"\$"),
    ("%", r"\%"),
    ("{", r"\{"),
    ("_", r"\_"),
    ("&", r"\&"),
    ("#", r"\#"),
    ("}", r"\}"),
    ("~", r"\textasciitilde"),
    ("'\"", r"'\,"),
    ("\"'", "\"\\,'"),
    ("Mr. ", r"Mr.\ "),
    ("Mrs. ", r"Mrs.\ ")]


def text_to_latex(text):
    #escape the special characters
    for l in latex_escape_table:
        text = text.replace(l[0], l[1])
    #attempt to deal with quotes
    text = re.sub(r"([\s])'", r"\1`", text)
    text = re.sub(r"([\s`])\"", r"\1``", text)
    text = re.sub(r"([\S])\"", r"\1''", text)
    text = text.replace(r"``\,'", r"``\,`")
    return text


def main():
    if (len(sys.argv) != 4 or
        not os.access(sys.argv[1], os.R_OK)):
        print "Usage: %s project_file first-page last-page" % sys.argv[0]
        sys.exit(-1)
    pd = project_data.ProjectData(sys.argv[1])
    pages = [X[0] for X in pd.get_pages("proof/jon")]
    idx_start = pages.index(sys.argv[2])
    idx_end = pages.index(sys.argv[3])
    for p in pages[idx_start : idx_end + 1]:
        print "%%page " + p + "%%"
        print text_to_latex(pd.get_text(p, "proof/jon")[project_data.DATA])


if __name__ == "__main__":
    main()
