#!/usr/bin/python3

import cgi
import cgitb
import sys
import json
import os
import xml.etree.cElementTree as et
import project
import re

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
            }


    def dispatch(self):
        verb = self.form.getfirst("verb")
        if not verb: raise CommandException(CommandException.NOVERB)
        if verb in self.ro_func_map:
            self.data = project.ProjectData(self.project_dir, True)
            self.data.unlock() #unlock immediately for read only cases
            self.ro_func_map[verb]()
        elif verb in rw_func_map:
            pass
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
        sys.stdout.buffer.write(b"Content-type: image/png\n\n" +
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
        def all_p(): return True
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        pf = all_p
        ident = self.data.first_page
        page_list = []
        while ident != None:
            if pf(): page_list.append(ident)
            ident = self.data.pages[ident].next_ident
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump(page_list, sys.stdout)


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
            "verb": "get_lines",
            "pageid": "001"
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

