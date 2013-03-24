#!/usr/bin/python3

import cgi
import cgitb
import sys
import json
import os
import xml.etree.cElementTree as et
import project
import re
import datetime

data_path = "../data/"

class CommandProcessor:

    def __init__(self, form):
        self.data = None
        projid = form.getfirst("projid")
        if not projid: raise CommandException(CommandException.NOPROJID)
        self.project_dir = os.path.abspath(os.path.join(data_path, projid))
        if not os.path.isdir(self.project_dir): raise CommandException(CommandException.BADPROJID)
        self.form = form
        if "REMOTE_USER" in os.environ:
            self.user = os.environ["REMOTE_USER"]
        else:
            self.user = os.environ["REMOTE_ADDR"]
        self.ro_func_map = {
            "get_meta": self.get_meta,
            "get_text": self.get_text,
            "get_image": self.get_image,
            "get_lines": self.get_lines,
            "status": self.status,
            "get_prev": self.get_prev,
            "get_next": self.get_next,
            "list": self.list
            }
        self.rw_func_map = {
            "reserve": self.reserve,
            "save": self.save
            }


    def dispatch(self):
        verb = self.form.getfirst("verb")
        if not verb: raise CommandException(CommandException.NOVERB)
        if verb in self.ro_func_map:
            self.data = project.ProjectData(self.project_dir, True)
            self.data.unlock() #unlock immediately for read only cases
            self.ro_func_map[verb]()
        elif verb in self.rw_func_map:
            self.data = project.ProjectData(self.project_dir)
            self.rw_func_map[verb]()
            self.data.unlock() #unlock after function call for write cases
        else:
            raise CommandException(CommandException.UNKNOWNVERB)


    def get_meta(self):
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump(self.data.meta, sys.stdout)


    def get_text(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        sys.stdout.buffer.write(b"Content-type: text/plain; charset=UTF-8\n\n" +
                                self.data.pages[pageid].get_text(self.user).encode("utf-8"))


    def get_image(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        exp = datetime.datetime.utcnow() + datetime.timedelta(days=364);
        sys.stdout.buffer.write(b"Content-type: image/png\n" +
                                b"Expires: " + exp.strftime("%a, %d %b %Y %H:%M:%S +0000").encode("ascii") +
                                b"\n\n" +
                                self.data.pages[pageid].get_image())


    def get_lines(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump(self.data.pages[pageid].image_lines, sys.stdout)


    def status(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        status = "unreserved"
        if self.user in self.data.pages[pageid].otext_filenames:
            if self.data.pages[pageid].otext_filenames[self.user] == None:
                status = "reserved"
            else:
                status = "submitted"
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump(status, sys.stdout)


    def get_prev(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump(self.data.pages[pageid].prev_ident, sys.stdout)


    def get_next(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump(self.data.pages[pageid].next_ident, sys.stdout)


    def list(self):
        reserved, submitted_diffs, submitted_nodiffs = [], [], []
        ident = self.data.first_page
        while ident != None:
            if self.user in self.data.pages[ident].otext_filenames:
                ts = self.data.pages[ident].otext_timestamps.get(self.user)
                ts = ts.ctime() if ts else ""
                o_filenames = self.data.pages[ident].otext_filenames
                if o_filenames[self.user] == None:
                    reserved.append((ident, ts))
                else:
                    if len(set([o_filenames[X]
                                for X in o_filenames
                                if o_filenames[X]])) < 2:
                        submitted_nodiffs.append((ident, ts))
                    else:
                        submitted_diffs.append((ident, ts))
            ident = self.data.pages[ident].next_ident
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump((reserved, submitted_diffs, submitted_nodiffs), sys.stdout)


    def reserve(self):
        ident = self.data.first_page
        policy = self.data.meta.get("policy")
        policy = int(policy) if policy else 1
        while ident != None:
            if (len(self.data.pages[ident].otext_filenames) < policy and
                self.user not in self.data.pages[ident].otext_filenames):
                self.data.pages[ident].add_otext(None, self.user)
                self.data.save()
                break
            ident = self.data.pages[ident].next_ident
        retval = "OK"
        if ident == None:
            retval = "COMPLETE"
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump(retval, sys.stdout)


    def save(self):
        retval = "OK"
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        text = self.form.getfirst("text")
        if len(text) > 10000: raise CommandException(CommandException.TOOLARGETEXT)
        self.data.pages[pageid].add_otext(text, self.user)
        self.data.save()
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump(retval, sys.stdout)


class CommandException(Exception):
    (UNKNOWN, NOVERB, UNKNOWNVERB, NOPROJID, NOPAGEID,
     TOOLARGETEXT, BADPAGEID, BADPROJID) = range(8)
    def __init__(self, code):
        self.code = code
    def __str__(self):
        return [
            "Unknown error",
            "No verb found",
            "Unknown verb",
            "No project identifier",
            "No page identifier",
            "Text too large",
            "Bad page identifier",
            "Bad project identifier"
            ][self.code]

##############################
#fake environment for testing.
#Comment out in final
class FakeForm:
    def getfirst(self, value):
        values = {
            "projid": "test",
            "verb": "get_image",
            "pageid": "001",
            "text": "Test text"
            }
        return values.get(value)
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

