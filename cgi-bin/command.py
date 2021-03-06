#!/usr/bin/python
# coding=utf-8

import cgi
import cgitb
import sys
import json
import os
import xml.etree.cElementTree as et
import project_data
import re
import difflib
import ghdiff

data_path = "../data/"



class CommandProcessor:

    re_tws = re.compile(r"[^\S\n]+\n", re.UNICODE) #whitespace excluding newlines followed by a newline
    re_sts = re.compile(r"[ \t]+") #sequence of spaces and tabs

    def __init__(self, form):
        projid = form.getfirst("projid")
        if not projid: raise CommandException(CommandException.NOPROJID)
        self.form = form
        #common fields-- task, user
        self.task = self.form.getfirst("task")
        if not self.task or self.task not in ("init", "preproof", "proof", "merge", "lines", "features"):
            raise CommandException(CommandException.NOTASK)
        self.user = self.task
        if self.user in ("proof", "feature"): #proof and feature are multi-user tasks, others are single user
            if os.environ.has_key("REMOTE_USER"):
                self.user += "/" + os.environ["REMOTE_USER"]
            else:
                self.user += "/" + os.environ["REMOTE_ADDR"]
        self.project_dir = os.path.join(data_path, projid)
        self.project_file = os.path.join(self.project_dir, "project")
        self.func_map = {
            "get": self.get,
            "list": self.list_pages,
            "save": self.save,
            "reserve": self.reserve,
            "diffs": self.diffs
            }


    def dispatch(self):
        verb = self.form.getfirst("verb")
        if not verb: raise CommandException(CommandException.NOVERB)
        if  verb not in self.func_map.keys():
            raise CommandException(CommandException.UNKNOWNVERB)
        self.func_map[verb]()


    def list_pages(self):
        listing = self.form.getfirst("type")
        if not listing: listing = "res"#default type is reserved
        data = project_data.ProjectData(self.project_file)#read lock
        pages = data.get_pages(self.user)
        data.unlock()
        page_list = []
        for pageid, status, timestamp in pages:
            if not data.exists(pageid, self.user): continue
            if listing == "done" and (status & project_data.STATUS_DONE):
                diffs_avbl = False
                if self.task == "proof":
                    sha1 = data.get_text_sha1(pageid, self.user)
                    for u in data.get_group(pageid, self.task):
                        if data.is_done(pageid, u) and data.get_text_sha1(pageid, u) != sha1:
                            diffs_avbl = True
                            break
                page_list.append((pageid, timestamp.strftime("%Y-%m-%d %H:%M"), diffs_avbl))
            elif listing == "res" and not (status & project_data.STATUS_DONE):
                page_list.append((pageid, timestamp.strftime("%Y-%m-%d %H:%M")))
        print "Content-type: text/json; charset=UTF-8\n"
        json.dump((listing, page_list), sys.stdout)


    def get(self):
        print "Content-type: application/json; charset=UTF-8\n"
        data = project_data.ProjectData(self.project_file)#read lock
        if self.task == "init":
            title = data.get_meta("title")
            if not title: title = ""
            project_page_link = data.get_meta("project_page")
            if not project_page_link: project_page_link = os.path.join(self.project_dir, "project.html")
            json.dump([title, project_page_link], sys.stdout)
        elif self.task in ("preproof", "proof"):
            pageid = self.form.getfirst("pageid")
            if not pageid: raise CommandException(CommandException.NOPAGEID)
            text_data = data.get_text(pageid, self.user)
            text = text_data[project_data.DATA] if text_data else ""
            is_baseline = False if data.is_done(pageid, self.user) else True
            images = [os.path.join(self.project_dir, X) if X else None
                        for X in data.get_images(pageid)[project_data.DATA]]
            validator = data.get_meta("validator")
            if not validator: validator = "../cgi-bin/proofing_validator.py"
            json.dump([pageid, text, images,
                       data.get_lines(pageid)[project_data.DATA],
                       data.get_meta("goodwords"),
                       validator,
                       is_baseline], sys.stdout)
        elif self.task == "lines":
            pageid = self.form.getfirst("pageid")
            if not pageid: raise CommandException(CommandException.NOPAGEID)
            image = os.path.join(self.project_dir, data.get_images(pageid)[project_data.DATA][1])
            json.dump([pageid, image, data.get_lines(pageid)[project_data.DATA]], sys.stdout)
        data.unlock()


    def diffs(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        data = project_data.ProjectData(self.project_file)#read lock
        data.unlock()
        proofers = [X for X in data.get_group(pageid, self.task) if data.is_done(pageid, X)]
        outstr = u"Content-type: text/html; charset=UTF-8\n\n"
        if len(proofers) > 1:
            rev_index = {}
            user_key = None
            for u in proofers:
                sha1 = data.get_text_sha1(pageid, u)
                if u == self.user: user_key = sha1
                if rev_index.has_key(sha1):
                    rev_index[sha1].append(u)
                else:
                    rev_index[sha1] = [u]
            if not user_key:
                outstr += "<p>No user version</p>"
            elif len(rev_index.keys()) == 1:
                outstr += "<p>%s identical versions</p>" % len(proofers)
            else:
                alt_versions = [X for X in rev_index.keys() if X != user_key]
                left_user = rev_index[user_key][0]
                left_text = unicode(data.get_text(pageid, left_user)[0], "utf8")
                left_user_string = ", ".join(rev_index[user_key]).replace(self.task + "/", "")
                if len(left_user_string) > 20: left_user_string = left_user_string[:20] + "..."
                for v in alt_versions:
                    right_user = rev_index[v][0]
                    right_text = unicode(data.get_text(pageid, right_user)[0], "utf8")
                    right_user_string = ", ".join(rev_index[v]).replace(self.task + "/", "")
                    if len(right_user_string) > 20: right_user_string = right_user_string[:20] + "..."
                    outstr += "".join(ghdiff.diff(left_text, right_text,
                                                  left_user_string,
                                                  right_user_string, 1))
        else:
            outstr += "<p>Only version</p>"
        sys.stdout.write(outstr.encode("utf8"))


    def save(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        if self.task == "lines":
            lines = self.form.getfirst("lines")
            if not lines:  raise CommandException(CommandException.NOLINES)
            lines = json.loads(lines)
            data = project_data.ProjectData(self.project_file, True)#write lock
            data.set_lines(pageid, lines, project_data.STATUS_DONE)
        else:
            text = self.form.getfirst("text")
            if not text: text = ""
            if len(text) > 10240: raise CommandException(CommandException.TOOLARGETEXT)
            text = self.re_tws.sub(r"\n", text).rstrip() #strip trailing EOL and EOS whitespace
            text = self.re_sts.sub(" ", text)#collapse sequences of spaces and tabs to a single space
            data = project_data.ProjectData(self.project_file, True)#write lock
            data.set_text(pageid, text, self.user)
        data.save() #unlock
        print "Content-type: application/json; charset=UTF-8\n"
        json.dump("OK", sys.stdout)


    def reserve(self):
        print "Content-type: application/json; charset=UTF-8\n"
        retval = "OK"
        data = project_data.ProjectData(self.project_file, True)#locks
        if self.task == "preproof":
            for pageid, status, timestamp in data.get_pages():
                if (not data.exists(pageid, self.user) and
                    data.is_done(pageid, "ocr")):
                    data.reserve(pageid, self.user, "ocr")
                    break
            else:
                retval = "COMPLETE"
        elif self.task == "proof":
            req_quality = data.get_meta("proof_quality")
            if not req_quality: req_quality = 3
            for pageid, status, timestamp in data.get_pages():
                if (not data.exists(pageid, self.user) and
                    data.is_done(pageid, "preproof") and
                    data.quality(pageid, "proof/")[1] < req_quality):
                    data.reserve(pageid, self.user, "preproof")
                    break
            else:
                for pageid, status, timestamp in data.get_pages():
                    if data.quality(pageid, "proof/")[0] < req_quality:
                        retval = "NONE_AVAILABLE"
                        break
                else:
                    retval = "COMPLETE"
        data.save() #unlocks
        json.dump(retval, sys.stdout)



class CommandException(Exception):
    (UNKNOWN, NOVERB, UNKNOWNVERB, NOPROJID, NOPAGEID,
     TOOLARGETEXT, BADPAGEID, BADPROJECTFILE,
     NOLINES, NOTASK) = range(10)
    def __init__(self, code):
        self.code = code
    def __repr__(self, code):
        return [
            "Unknown error",
            "No verb found",
            "Unknown verb",
            "No project identifier",
            "No page identifier",
            "Text too large",
            "Bad page identifier",
            "Project file does not exist",
            "No lines list sent",
            "No task identifier sent"
            ][code]

##############################
#fake environment for testing.
#Comment out in final
class FakeForm:
    def getfirst(self, value):
        values = {
            "projid": "jane-eyre",
            "verb": "diffs",
            # "lines" : [1000, 2000, 3000],
            "pageid" : "007",
            # "text": "This is a yet another test",
            "task": "proof",
            "type": "done"
            }
        if value in values.keys():
            return values[value]
        else:
            return None
#
##############################

def main():
    if  "test" in sys.argv:
        form = FakeForm()
        os.environ["REMOTE_ADDR"] = "127.0.0.3"
        os.environ["REMOTE_USER"] = "jon"
    else:
        cgitb.enable()
        form = cgi.FieldStorage()
    CommandProcessor(form).dispatch()



if __name__ == "__main__":
    main()

