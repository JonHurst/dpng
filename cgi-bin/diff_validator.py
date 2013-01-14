#!/usr/bin/python
# coding=utf-8

import cgi
import cgitb
import subprocess
import sys
import re
import tokenise
import difflib


def calculate_classes(tokens, check_tokens):
    seq_tokens = tuple([tuple(X) for X in tokens])
    seq_check = tuple([tuple(X) for X in check_tokens])
    sm = difflib.SequenceMatcher(None, seq_tokens, seq_check, False)
    non_matching_tokens = set(range(len(seq_tokens)))
    for mb in sm.get_matching_blocks():
        if mb[2] == 0: break
        start_match, end_match = sys.maxint, 0
        for c in range(mb[0], mb[0] + mb[2]):
            non_matching_tokens.remove(c)
            if not tokens[c][1] & tokenise.TYPE_LINEBREAK:
                start_match = min(start_match, c)
                end_match = max(end_match, c)
        if start_match != sys.maxint:
            tokens[start_match].append("start_match")
        if end_match != 0:
            tokens[end_match].append("end_match")
    for c, t in enumerate(tokens):
        if (not (t[1] & tokenise.TYPE_LINEBREAK)) and c in non_matching_tokens:
            tokens[c].append("nomatch")
        if t[1] & tokenise.TYPE_PUNC:
            tokens[c].append("punc")
        elif t[1] & tokenise.TYPE_NOTE:
            tokens[c].append("note")
        elif t[1] & tokenise.TYPE_DIGIT:
            tokens[c].append("digit")


def build_text(tokens):
    token_join = ""
    for t in tokens:
        if t[1] & tokenise.TYPE_PARABREAK:
            t[0] += "\n"
        if len(t) > 2: #classes appended
            token_join += "<span class='%s'>%s</span>" % (" ".join(t[2:]), cgi.escape(t[0]))
        elif t[1] & tokenise.TYPE_WORD:
            token_join += "<span>" + cgi.escape(t[0]) + "</span>"
        else:
            token_join += cgi.escape(t[0])

    output = ""
    for line in token_join.splitlines():
        if len(line):
            output += "<div class='line'>" + line + "</div>\n"
        else:
            output += "<div class='blank'></div>\n"
    return "<!--%s--><div id='text'>\n%s</div>" % (serial, output)


if len(sys.argv) == 2 and sys.argv[1] == "test":
    text=u"""\

“”‘’

INTRODUCTION [**Note]

caféq, The fol1owing. narrative falls naturally into three
divisions, corresponding to distinct and clearly
marked periods of Sophy's life. Of the first and
second-her childhood at Mrpingham and her so-
journ in Paris--the records are fragmentary, and"""
    check_text=u"""\

“”‘’

INTRODUCTION [**Note]

café, The following. narrative falls naturally into three
divisions, corresponding to distinct and clearly
marked periods of Sophy's life. Of the first and
second-her childhood at Morpingham and her so-
journ in Pavis--the records are fragmentary, and"""
    goodwords = ""
    serial = "1234"
else:
    cgitb.enable()
    form = cgi.FieldStorage()
    if not form.has_key('text'):
        text = u""
    else:
        text = unicode(form['text'].value, "utf-8")
    serial = form.getfirst("serial", "0000")
    projid = form.getfirst("projid", "")
    page_id = form.getfirst("page_id", "")
    check_text = unicode(file("../data/%s/alt-ed/%s" % (projid, page_id)).read(), "utf-8")

print "Content-type: text/html; charset=UTF-8\n"
translate_table = dict(zip([ord(X) for X in u"“”‘’"], [ord(X) for X in u"\"\"''"]))
tokens = tokenise.tokenise(text.translate(translate_table))[:-1]
check_tokens = tokenise.tokenise(check_text.translate(translate_table))[:-1]
calculate_classes(tokens, check_tokens)
sys.stdout.write(build_text(tokens).encode("utf-8"))




