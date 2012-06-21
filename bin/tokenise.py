#!/usr/bin/python

import re

TYPE_UNKNOWN, TYPE_WORD, TYPE_DIGIT, TYPE_SPACE, TYPE_PUNC, TYPE_NOTE, TYPE_PAGEMARKER = range(7)

def tokenise(text, pagemarkers=False):
    tokens = []
    regexp_notes = re.compile(r"(\[\*\*[^\]]*\])", re.UNICODE)
    regexp_words = re.compile(r"([^\W_]+)", re.UNICODE)
    regexp_digits = re.compile(r"([\d]+)", re.UNICODE)
    regexp_whitespace = re.compile(r"([\s]+)", re.UNICODE)
    regexp_pagemarker = re.compile(r"(\%\%page[^\n]*\n)", re.UNICODE)

    def process_digits(text):
        text_sections = regexp_digits.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                tokens.append([s, TYPE_DIGIT])
            else:
                tokens.append([s, TYPE_WORD])

    def process_words(text):
        text_sections = regexp_words.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                process_digits(s)
            else:
                process_whitespace(s)

    def process_whitespace(text):
        text_sections = regexp_whitespace.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                tokens.append([s, TYPE_SPACE])
            else:
                tokens.append([s, TYPE_PUNC])

    def process_notes(text):
        text_sections = regexp_notes.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                tokens.append([s, TYPE_NOTE])
            else:
                process_words(s)

    def process_pagemarkers(text):
        text_sections = regexp_pagemarker.split(text)
        for c, s in enumerate(text_sections):
            if c % 2:
                tokens.append([s, TYPE_PAGEMARKER])
            else:
                process_notes(s)

    if pagemarkers:
        process_pagemarkers(text)
    else:
        process_notes(text)
    return [X for X in tokens if len(X[0])]
