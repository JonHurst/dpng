#!/usr/bin/python3

import cgi
import cgitb
import os
import sys
import project
import difflib
import xml.sax.saxutils
import re
from command import CommandException

data_path = "../data/"

def escape(text):
    return xml.sax.saxutils.escape(text, {" ": " "})


def diff(a, b):
    a = a.splitlines()
    b = b.splitlines()
    return "\n".join(colorize(list(difflib.unified_diff(a, b, n=1))))


def colorize(lines):
    lines.reverse()
    while lines and not lines[-1].startswith("@@"):
        lines.pop()
    line_number = 0
    re_ln = re.compile(r"@@ -(\d+)")
    while lines:
        line = lines.pop()
        if line.startswith("@@"):
            if line_number > 0:
                yield "</div>"
            line_number = int(re_ln.search(line).group(1))
            yield "<h3>" + line.replace("@", " ") + "</h3><div>"
        elif line.startswith("-"):
            if lines:
                _next = []
                while lines and len(_next) < 2:
                    _next.append(lines.pop())
                if _next[0].startswith("+") and (len(_next) == 1
                    or _next[1][0] not in ("+", "-")):
                    aline, bline = _line_diff(line[1:], _next.pop(0)[1:])
                    yield '<div class="delete"><span class="ln">%s</span>-%s</div>' % (line_number, aline)
                    line_number += 1
                    yield '<div class="insert"><span class="ln">&nbsp;</span>+%s</div>' % (bline,)
                    if _next:
                        lines.append(_next.pop())
                    continue
                lines.extend(reversed(_next))
                yield '<div class="delete"><span class="ln">%s</span>%s</div>' % (line_number, escape(line))
                line_number += 1
        elif line.startswith("+"):
            yield '<div class="insert"><span class="ln">&nbsp;</span>' + escape(line) + '</div>'
        else:
            yield '<div><span class="ln">%s</span>%s</div>' % (line_number, escape(line))
            line_number += 1
    yield "</div>"



def _line_diff(a, b):
    aline = []
    bline = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b).get_opcodes():
        if tag == "equal":
            aline.append(escape(a[i1:i2]))
            bline.append(escape(b[j1:j2]))
            continue
        aline.append('<span class="highlight">%s</span>' % (escape(a[i1:i2]),))
        bline.append('<span class="highlight">%s</span>' % (escape(b[j1:j2]),))
    return "".join(aline), "".join(bline)



def build_diff_report(form):
    projid = form.getfirst("projid")
    if not projid: raise CommandException(CommandException.NOPROJID)
    project_dir = os.path.abspath(os.path.join(data_path, projid))
    if not os.path.isdir(project_dir): raise CommandException(CommandException.BADPROJID)
    pageid = form.getfirst("pageid")
    if not pageid: raise CommandException(CommandException.NOPAGEID)
    user = os.environ["REMOTE_ADDR"]
    if "REMOTE_USER" in os.environ:
        user = os.environ["REMOTE_USER"]
    data = project.ProjectData(project_dir, True)
    data.unlock() #unlock immediately since read only
    otext_dict = data.pages[pageid].otext_filenames
    if user not in otext_dict:
        return "<p>No user version</p>"
    if len(otext_dict) == 1:
        return "<p>Only version</p>"
    user_file = otext_dict[user]
    other_files = set([otext_dict[X] for X in otext_dict if otext_dict[X]])
    other_files -= set([user_file])
    if(len(other_files) == 0):
        return "<p>%s identical versions</p>" % len(otext_dict)
    user_text = open(os.path.join(data.pages[pageid].base_dir,
                                  user_file), encoding="utf-8").read()
    outstr = ""
    for f in other_files:
        other_text = open(os.path.join(data.pages[pageid].base_dir,
                                  f), encoding="utf-8").read()
        outstr += diff(user_text, other_text)
    return outstr


##############################
#fake environment for testing.
#Comment out in final
class FakeForm:
    def getfirst(self, value):
        values = {
            "projid": "test",
            "pageid": "001",
            }
        return values.get(value)
#
##############################

def main():
    if  "test" in sys.argv:
        form = FakeForm()
        os.environ["REMOTE_ADDR"] = "127.0.0.1"
        # os.environ["REMOTE_USER"] = "jon"
    else:
        cgitb.enable()
        form = cgi.FieldStorage()
    sys.stdout.buffer.write(b"Content-type: text/html; charset=UTF-8\n\n" +
                            build_diff_report(form).encode("utf-8"));



if __name__ == "__main__":
    main()

