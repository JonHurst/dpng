#!/usr/bin/python
# coding=utf-8

import cgi
import cgitb
import subprocess
import sys
import re

TYPE_UNKNOWN, TYPE_WORD, TYPE_DIGIT, TYPE_SPACE, TYPE_PUNC, TYPE_NOTE = range(6)
# descriptors = ["Unknown", "Word", "Digit", "Whitespace", "Punctuation", "Note"]

stealth_scannos = set(["he", "be", "de", "do"])

def aspell_text(text, goodwords):
    goodwords = set(unicode(goodwords, "utf-8").split(";"))
    aspell_output_en = subprocess.Popen(["/usr/bin/aspell", "list", "--encoding=utf-8", "--lang=en"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE
                                     ).communicate(text.encode("utf-8"))[0]
    aspell_output_fr = subprocess.Popen(["/usr/bin/aspell", "list", "--encoding=utf-8", "--lang=fr"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE
                                     ).communicate(text.encode("utf-8"))[0]
    en_errors = set(unicode(aspell_output_en, "utf-8").splitlines())
    fr_errors = set(unicode(aspell_output_fr, "utf-8").splitlines())
    #french reports error in hyphenated word as whole hyphenated word e.g. zbreakfast-room. Since we
    #tokenise "-" as punctuation, we need to find out if either side is a spelling error. English seems
    #to do this already.
    hyphenated = u""
    for e in fr_errors:
        if "-" in e: hyphenated += e.replace("-", " ") + " "
    if hyphenated:
        aspell_output_fr_hyph = subprocess.Popen(["/usr/bin/aspell", "list", "--encoding=utf-8", "--lang=fr"],
                                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE
                                                 ).communicate(hyphenated.encode("utf-8"))[0]
        fr_errors_hyph = set(unicode(aspell_output_fr_hyph, "utf-8").splitlines())
        fr_errors |= fr_errors_hyph
    return (en_errors & fr_errors)  - goodwords


def tokenise(text):
    tokens = []
    regexp_notes = re.compile(r"(\[\*\*[^\]]*\])", re.UNICODE)
    regexp_words = re.compile(r"([^\W_]+)", re.UNICODE)
    regexp_digits = re.compile(r"([\d]+)", re.UNICODE)
    regexp_whitespace = re.compile(r"([\s]+)", re.UNICODE)

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

    text_sections = regexp_notes.split(text)
    for c, s in enumerate(text_sections):
        if c % 2:
            tokens.append([s, TYPE_NOTE])
        else:
            process_words(s)
    return [X for X in tokens if len(X[0])]


def apply_language_specials(tokens):
    #join word + punctuation=="'" + word into single word
    for c in range(len(tokens) - 2):
        if (tokens[c][1] == TYPE_WORD and
            tokens[c + 1][0] == "'" and
            tokens[c + 2][1] == TYPE_WORD):
            tokens[c] = [tokens[c][0] + tokens[c + 1][0] + tokens[c + 2][0], TYPE_WORD]
            tokens[c + 1] = tokens[c + 2] = ["", TYPE_UNKNOWN]
    return [X for X in tokens if X[1] != TYPE_UNKNOWN]


def calculate_classes(tokens, spelling_errors, stealth_scannos):
    tokens.insert(0, ["", TYPE_SPACE])
    tokens.append(["\n", TYPE_SPACE])
    for c, t in enumerate(tokens):
        if t[1] == TYPE_PUNC:
            tokens[c].append("punc")
            end_char = tokens[c][0][-1]
            #hyphen at end of line
            if (#(t[0].endswith("-") and tokens[c+1][0] == "\n") or
                #punctuation with space both sides that is not a 3 dot  ellipsis
                (tokens[c][0] != "..." and tokens[c-1][1] == TYPE_SPACE and tokens[c+1][1] == TYPE_SPACE) or
                #end of word punctuation without a following space
                (end_char in ":;!?" and tokens[c + 1][1] != TYPE_SPACE) or
                # . and , that are not followed by a space and are not single and followed by a number
                (end_char in ".," and tokens[c + 1][1] != TYPE_SPACE and not
                 (len(tokens[c][0]) == 1 and tokens[c + 1][1] == TYPE_DIGIT)) or
                # , at end of paragraph
                (end_char == "," and tokens[c + 1][0] == "\n\n")):
                tokens[c].append("error")
            #warn of full stop followed by whitespace then lower case letter or comma followed whitespace
            #then an upper case letter
            if (end_char in ".," and c < len(tokens) - 2 and
                tokens[c + 1][1] == TYPE_SPACE and tokens[c + 2][1] == TYPE_WORD):
                ch = tokens[c + 2][0][0]
                if ((end_char == "." and ch.islower()) or
                    (end_char == "," and ch.isupper() and tokens[c + 2][0] != "I")):
                        tokens[c].append("warn")
        elif t[1] == TYPE_WORD:
            if t[0] in spelling_errors:
                tokens[c].append("spell")
            elif t[0] in stealth_scannos:
                tokens[c].append("stealth")
        elif t[1] == TYPE_NOTE:
            tokens[c].append("note")
        elif t[1] == TYPE_DIGIT:
            tokens[c].append("digit")
    del tokens[-1]


def build_text(tokens):
    token_join = ""
    for t in tokens:
        if len(t) > 2: #classes appended
            token_join += "<span class='%s'>%s</span>" % (" ".join(t[2:]), cgi.escape(t[0]))
        elif t[1] == TYPE_WORD:
            token_join += "<span>" + cgi.escape(t[0]) + "</span>"
        else:
            token_join += cgi.escape(t[0])
    output = ""
    for line in token_join.splitlines():
        if len(line):
            output += "<div class='line'>" + line + "</div>\n"
        else:
            output += "<div class='blank'></div>\n"
    return "<div id='text'>\n" + output + "</div>"


if len(sys.argv) == 2 and sys.argv[1] == "test":
    text=u"""\
habituée zbreakfast-room
this_#is an error . here
this is not a $5,000.00 error
[**Note2]

INTRODUCTION [**Note]

caféq, The fol1owing. narrative falls naturally into three
divisions, corresponding to distinct and clearly
marked periods of Sophy's life. Of the first and
second-her childhood at Morpingham and her so-
journ in Paris--the records are fragmentary, and
tradition does little to supplement them. As regards
Morpingham, the loss is small. The annals of a little'
maid-servant may be left in vagueness without much
loss. Enough remains to show both the manner of
child Sophy was and how it fell out that she spread
her wings and left the Essex village far behind her.
It is a different affair when we come to the French
<em>period</em>. The years spent in and near Paris, in the
care and under the roof of Lady Margaret Dudding-
ton, were of crucial moment in Sophy's development.
They changed her from what she had been and made
her what she was to be. Without Paris, Kravo-
nia, still extraordinary, would have been impossible.

Yet the surviving history of Paris and the life
there is scanty. Only a sketch is possible. A rec-
ord existed-and a fairly full one-in the Julia Rob-
ins correspondence; that we know from Miss Rob-
ins herself. But the letters written from Paris
by Sophy to her lifelong friend have, with some
few exceptions, perished. Miss Robins accounts for
this-and in view of her careful preservation of
later correspondence, her apology must be accept-"""
    goodwords = ""
else:
    # cgitb.enable()
    form = cgi.FieldStorage()
    goodwords = form.getfirst("goodwords", "")
    if not form.has_key('text'):
        text = u""
    else:
        text = unicode(form['text'].value, "utf-8")
print "Content-type: text/html; charset=UTF-8\n"
spelling_errors = aspell_text(text, goodwords)
tokens = apply_language_specials(tokenise(text))
calculate_classes(tokens, spelling_errors, stealth_scannos)
sys.stdout.write(build_text(tokens).encode("utf-8"))




