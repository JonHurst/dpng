#!/usr/bin/python

import project_data
import sys
import difflib
import cgi
import cgitb
import os

data_path = "../data/"


xhtml_template = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Diff report</title>
    <link rel="stylesheet" type="text/css" href="../css/diff_report.css"/>
  </head>
  <body>
  <h1>Diff Report</h1>
  %s
  </body>
</html>"""

def create_html(project_file):
    outstr = ""
    data = project_data.ProjectData(project_file)
    data.unlock()
    for page in [X[0] for X in data.get_pages()]:
        group = [X for X in data.get_group(page, "proof") if data.is_done(page, X)]
        diff = difflib.HtmlDiff()
        if len(group) > 1:
            outstr += "<h2>Page %s</h2><p>(%s users)</p>" % (page, len(group))
            rev_index = {}
            for u in group:
                sha1 = data.get_text_sha1(page, u)
                if rev_index.has_key(sha1):
                    rev_index[sha1].append(u)
                else:
                    rev_index[sha1] = [u]
            if len(rev_index.keys()) == 1:
                outstr += "<p>Text identical</p>"
            else:
                l = [(len(rev_index[X]), X) for X in rev_index.keys()]
                l.sort()
                l.reverse()
                for a in l[1:]:
                    left_user = rev_index[l[0][1]][0]
                    right_user = rev_index[a[1]][0]
                    left_text = data.get_text(page, left_user)[0]
                    right_text = data.get_text(page, right_user)[0]
                    diff_table = diff.make_table(left_text.splitlines(),
                                                 right_text.splitlines(),
                                                 rev_index[l[0][1]],
                                                 rev_index[a[1]],
                                                 True, 2)
                    outstr += diff_table
    return outstr


cgitb.enable()
form = cgi.FieldStorage()
projid = form.getfirst("projid")
if not projid: projid = "jane-eyre"

print "Content-type: text/html; charset=UTF-8\n"
print xhtml_template % create_html(os.path.join(data_path, projid, "project"))



