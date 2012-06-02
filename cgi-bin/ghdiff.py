import difflib
import os.path
import xml.sax.saxutils
import re

def escape(text):
    return xml.sax.saxutils.escape(text, {" ": "&nbsp;"})


def diff(a, b, user_a, user_b, n=3):
    if isinstance(a, basestring):
        a = a.splitlines()
    if isinstance(b, basestring):
        b = b.splitlines()
    return "\n".join(colorize(list(difflib.unified_diff(a, b, n=n)), user_a, user_b))


def colorize(diff, user_a, user_b):
    if isinstance(diff, basestring):
        lines = diff.splitlines()
    else:
        lines = diff
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
            line = "%s vs %s (%s)" % (user_a, user_b, line.replace("@", ""))
            yield '<h3><a href="#">' + escape(line) + "</a></h3><div>"
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


