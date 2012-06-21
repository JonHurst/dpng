#!/usr/bin/python

import sys
import os
import subprocess
import project_data
from tokenise import *


def check_dict(word):
    aspell_output= subprocess.Popen(["/usr/bin/aspell", "pipe", "--encoding=utf-8", "--lang=en", "--dont-suggest"],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE
                                    ).communicate(word.encode("utf-8"))[0]
    if aspell_output.find("*") != -1:
        return True
    return False


def sort_func(item1, item2):
    if item1 == item2: return 0
    item1 = item1.split(None, 2)[:2]
    item1.reverse()
    item2 = item2.split(None, 2)[:2]
    item2.reverse()
    if(item1 < item2): return -1
    return 1

#check command line
if (len(sys.argv) <4 or
    not os.access(sys.argv[1], os.R_OK)):
    print "Usage: %s project_file user [old_file]" % sys.argv[0]
    sys.exit(-1)
#get a list of relevant pages
pd = project_data.ProjectData(sys.argv[1])
pages = pd.get_pages(sys.argv[2])
if len(pages) == 0:
    print "No pages for user " + sys.argv[2]
    sys.exit(-2)
#build the pages into a single block of text
text = u""
for p in pages:
    text += unicode(pd.get_text(p[0], sys.argv[2])[project_data.DATA], "utf-8")
    text += u"\n"
#tokenise the text
tokens = tokenise(text)
#make apostrophes and hyphens part of words
for c in range(len(tokens) - 2):
    if (tokens[c][1] == TYPE_WORD and
        (tokens[c + 1][0] == "'" or tokens[c + 1][0] == "-") and
        tokens[c + 2][1] == TYPE_WORD):
        tokens[c + 2] = [tokens[c][0] + tokens[c + 1][0] + tokens[c + 2][0], TYPE_WORD]
        tokens[c] = tokens[c + 1] = ["", TYPE_UNKNOWN]
tokens = [X for X in tokens if X[1] != TYPE_UNKNOWN]
#split out eol hyphenated words
eol_hyphenated = set()
for c in range(len(tokens) - 3):
    if (tokens[c][1] == TYPE_WORD and
          tokens[c + 1][0] == "-" and
          tokens[c + 2][0] == "\n" and
          tokens[c + 3][1] == TYPE_WORD):
        eol_hyphenated.add(tokens[c][0] + tokens[c + 1][0] + tokens[c + 3][0])
        tokens[c] = tokens[c + 1] = tokens[c + 2] = tokens[c + 3] = ["", TYPE_UNKNOWN]
tokens = [X for X in tokens if X[1] != TYPE_UNKNOWN]
#build the word index
word_index = {}
for t in tokens:
    if t[1] == TYPE_WORD:
        if word_index.has_key(t[0]):
            word_index[t[0]] += 1
        else:
            word_index[t[0]] = 1
#build man index
man_index = {}
if os.access(sys.argv[3], os.R_OK):
    for l in file(sys.argv[3]):
        if l.find("#man#") != -1:
            man_index[l.split()[0]] = l.strip()
#classify the hyphens
outlines = []
for s in eol_hyphenated:
    if man_index.has_key(s):
        outlines.append(man_index[s])
        continue
    unhyphenated = s.replace("-", "")
    if word_index.has_key(s) and not word_index.has_key(unhyphenated):
        outlines.append(s + " : " + s)
    elif not word_index.has_key(s) and word_index.has_key(unhyphenated):
        outlines.append(s + " : " + unhyphenated)
    elif word_index.has_key(s) and word_index.has_key(unhyphenated):
        ver1, ver2 = s, unhyphenated
        if word_index[s] < word_index[unhyphenated]:
            ver1, ver2 = unhyphenated, s
        outlines.append(u"%s #amb# %s %d-vs-%d %s" % (
                s, ver1, word_index[ver1], word_index[ver2],ver2))
    else:
        if check_dict(unhyphenated):
            outlines.append(s + " #dict# " + unhyphenated)
        else:
            outlines.append(s + " #nodata# " + s)
#sort and output
outlines.sort(sort_func)
for l in outlines:
    sys.stdout.write((l + "\n").encode("utf-8"))

