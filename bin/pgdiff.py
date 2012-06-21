#!/usr/bin/python

import difflib
import sys
import re
from tokenise import *

def language_specials(tokens):
    #make apostrophes and hyphens part of words
    for c in range(len(tokens) - 2):
        if (tokens[c][1] == TYPE_WORD and
            (tokens[c + 1][0] == "'" or tokens[c + 1][0] == "-") and
            tokens[c + 2][1] == TYPE_WORD):
            tokens[c + 2] = [tokens[c][0] + tokens[c + 1][0] + tokens[c + 2][0], TYPE_WORD]
            tokens[c] = tokens[c + 1] = ["", TYPE_UNKNOWN]
    return [X for X in tokens if X[1] != TYPE_UNKNOWN]


def remove_soft_hyphens(soft_hyphen_dict, tokens):
    for c in range(len(tokens) - 3):
        if (tokens[c][1] == TYPE_WORD and
            tokens[c + 1][0] == "-" and
            tokens[c + 2][0] == "\n" and
            tokens[c + 3][1] == TYPE_WORD):
            word = tokens[c][0] + tokens[c + 1][0] + tokens[c + 3][0]
            tokens[c] = [soft_hyphen_dict[word], TYPE_WORD]
            tokens[c + 1] = tokens[c + 2] = tokens[c + 3] = ["", TYPE_UNKNOWN]
    return [X for X in tokens if X[1] != TYPE_UNKNOWN]


def join_hyphens(tokens):
    for c in range(len(tokens) - 3):
        if (tokens[c][1] == TYPE_WORD and
            tokens[c + 1][0] == "-" and
            tokens[c + 2][0] == "\n" and
            tokens[c + 3][1] == TYPE_WORD):
            tokens[c] = [tokens[c][0] + tokens[c + 1][0] + tokens[c + 3][0], TYPE_WORD]
            tokens[c + 1] = tokens[c + 2] = tokens[c + 3] = ["", TYPE_UNKNOWN]
    return [X for X in tokens if X[1] != TYPE_UNKNOWN]


def make_sequence(tokens):
    tokens.insert(0, ["", TYPE_UNKNOWN])
    tokens.append(["", TYPE_UNKNOWN])
    sequence = []
    for c, t in enumerate(tokens):
        if t[1] == TYPE_SPACE:
            if t[0].find("\n\n") != -1:
                sequence.append("\n")
            elif t[0] == "\n" and (tokens[c - 1][0][-1] == "-" or tokens[c + 1][0] == "--"):
                pass
            else:
                sequence.append(" ")
        elif t[1] == TYPE_WORD or t[1] == TYPE_DIGIT or t[1] == TYPE_PUNC:
            sequence.append(t[0])
    return sequence


def split_chapters(text):
    text = text.replace("_", "").replace("\"", "'")
    chapters = re.split("^Chapter ", text, flags=re.IGNORECASE|re.MULTILINE)
    return [chapters[0]] + ["Chapter " + X for X in chapters[1:]]


if len(sys.argv) < 4:
    print "Usage: %s my_file their_file soft_hyphens_file"
    sys.exit(-1)

soft_hyphen_dict = {}
for line in file(sys.argv[3]):
    fields = unicode(line, "utf-8").split()
    soft_hyphen_dict[fields[0]] = fields[2]

sm = difflib.SequenceMatcher()


chapters_1 = split_chapters(unicode(file(sys.argv[1]).read(), "utf-8"))
chapters_2 = split_chapters(unicode(file(sys.argv[2]).read(), "utf-8"))
chapter_str = []
for ch in range(20):
    seq1 = make_sequence(remove_soft_hyphens(soft_hyphen_dict, language_specials(tokenise(chapters_1[ch]))))
    seq2 = make_sequence(join_hyphens(language_specials(tokenise(chapters_2[ch]))))

    sm.set_seqs(seq1, seq2)

    outstr = u"<p>"
    matches = sm.get_matching_blocks()
    for c, m in enumerate(matches):
        if m[2] == 0: break #m[2] is count of matching paras
        next_match = matches[c + 1]
        outstr += "".join(seq1[m[0]:m[0] + m[2]]).replace("\n", "</p><p>")
        diff1 = seq1[m[0] + m[2]: next_match[0]]
        for t in diff1:
            if t == "\n": t = "\\n"
            outstr += "<span class='diff1'>%s</span>" % t
        diff2 = seq2[m[1] + m[2]: next_match[1]]
        for t in diff2:
            if t == "\n": t = "\\n"
            outstr += "<span class='diff2'>%s</span>" % t
    outstr += "</p>"
    chapter_str.append(outstr)


output = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>PG Diff</title>
    <style type="text/css">
p{ color: gray;}
.chapter{font-family: 'Droid Sans Mono', monospace;
    max-width: 45em; margin: auto;}
.diff1{color: black; background-color: #FFA0A0;}
.diff2{color: black; background-color: #A0FFA0;}
    </style>
  </head>
  <body>
<div class="chapter">%s</div>
  </body>
</html>""" % "</div><div class='chapter'>".join(chapter_str)

sys.stdout.write(output.encode("utf-8"))
