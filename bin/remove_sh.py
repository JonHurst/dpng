#!/usr/bin/python

import sys
from tokenise import *
import re

def language_specials(tokens):
    #make apostrophes and hyphens part of words
    for c in range(len(tokens) - 2):
        if (tokens[c][1] == TYPE_WORD and
            (tokens[c + 1][0] == "'" or tokens[c + 1][0] == "-") and
            tokens[c + 2][1] == TYPE_WORD):
            tokens[c + 2] = [tokens[c][0] + tokens[c + 1][0] + tokens[c + 2][0], TYPE_WORD]
            tokens[c] = tokens[c + 1] = ["", TYPE_UNKNOWN]
    return [X for X in tokens if X[1] != TYPE_UNKNOWN]


def process_hyphens(soft_hyphen_dict, tokens):
    for c in range(len(tokens) - 3):
        if (tokens[c][1] == TYPE_WORD and
            tokens[c + 1][0] == "-" and
            tokens[c + 2][0] == "\n" and
            (tokens[c + 3][1] == TYPE_WORD or tokens[c + 3][1] == TYPE_PAGEMARKER)):
            word = tokens[c][0] + tokens[c + 1][0]
            if tokens[c + 3][1] == TYPE_PAGEMARKER:
                if len(tokens) < c + 4: continue
                word += tokens[c + 4][0]
            else:
                word += tokens[c + 3][0]
            if word == soft_hyphen_dict[word]:
                tokens[c + 1][0] += u"%"
            else:
                tokens[c + 1][0] = u"%"
    return tokens


text = unicode(sys.stdin.read(), "utf-8")


soft_hyphen_dict = {}
for line in file(sys.argv[1]):
    fields = unicode(line, "utf-8").split()
    soft_hyphen_dict[fields[0]] = fields[2]

tokens = language_specials(tokenise(text, True))
tokens = process_hyphens(soft_hyphen_dict, tokens)
for t in tokens:
    sys.stdout.write(t[0].encode("utf-8"))
