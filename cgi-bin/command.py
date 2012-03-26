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

data_path = "../data/"



class CommandProcessor:

    re_tws = re.compile(r"[^\S\n]+\n", re.UNICODE) #whitespace excluding newlines followed by a newline

    def __init__(self, form):
        projid = form.getfirst("projid")
        if not projid: raise CommandException(CommandException.NOPROJID)
        self.form = form
        self.project_dir = os.path.join(data_path, projid)
        self.data = project_data.ProjectData(os.path.join(self.project_dir, "project"))
        self.func_map = {
            "get": self.get,
            "list": self.list_pages,
            "save": self.save,
            "lines": self.update_lines,
            "reserve": self.reserve
            }


    def dispatch(self):
        verb = self.form.getfirst("verb")
        if not verb: raise CommandException(CommandException.NOVERB)
        if  verb not in self.func_map.keys():
            raise CommandException(CommandException.UNKNOWNVERB)
        self.func_map[verb]()


    def list_pages(self):
        available, done = [], []
        user = self.form.getfirst("user")
        if not user: user = os.environ["REMOTE_ADDR"]
        for pageid, status, timestamp in self.data.get_pages(user):
            table = done if status & project_data.STATUS_DONE else available
            table.append(
                ("<tr>"
                 "<td><a href='%(pageid)s'>%(pageid)s</a></td>"
                 "<td>%(timestamp)s</td>"
                 "</tr>" % {"pageid": pageid, "timestamp": timestamp.strftime("%Y-%m-%d %H:%M")}))
        template = "<h1>%s</h1><table>%s</table>"
        available = template % ("Available", "".join(available)) if available else ""
        done = template % ("Done", "".join(done)) if done else ""
        print "Content-type: text/html; charset=UTF-8\n"
        print "<div id='pagepicker_tables'>", available, done, "</div>"


    def get(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        print "Content-type: application/json; charset=UTF-8\n"
        text_data = self.data.get_text(pageid, os.environ["REMOTE_ADDR"])
        json.dump([pageid, self.data.get_meta("title"), text_data[project_data.DATA],
                   [os.path.join(self.project_dir, X) if X else None
                    for X in self.data.get_images(pageid)[project_data.DATA]],
                   self.data.get_lines(pageid)[project_data.DATA]], sys.stdout)


    def save(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        text = self.form.getfirst("text")
        if not text: text = ""
        if len(text) > 10240: raise CommandException(CommandException.TOOLARGETEXT)
        text = self.re_tws.sub(r"\n", text).rstrip() #strip trailing EOL and EOS whitespace
        self.data.set_text(pageid, text, os.environ["REMOTE_ADDR"])
        self.data.save()
        print "Content-type: application/json; charset=UTF-8\n"
        json.dump("OK", sys.stdout)


    def update_lines(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        lines = self.form.getfirst("lines")
        if not lines:  raise CommandException(CommandException.NOLINES)
        lines = json.loads(lines)
        self.data.set_lines(pageid, lines, project_data.STATUS_DONE)
        self.data.save()
        print "Content-type: application/json; charset=UTF-8\n"
        json.dump("OK", sys.stdout)


    def reserve(self):
        #TODO: reserve just reserves all pages to the user for now. Add
        #routine to identify and reserve a single page later
        for pageid, status, timestamp in self.data.get_pages():
            username = os.environ["REMOTE_ADDR"]
            self.data.reserve(pageid, username)
        self.data.save()
        print "Content-type: application/json; charset=UTF-8\n"
        json.dump("OK", sys.stdout)



class CommandException(Exception):
    (UNKNOWN, NOVERB, UNKNOWNVERB, NOPROJID, NOPAGEID,
     TOOLARGETEXT, BADPAGEID, BADPROJECTFILE,
     NOLINES) = range(9)
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
            "No lines list sent"
            ][code]

##############################
#fake environment for testing.
#Comment out in final
class FakeForm:
    def getfirst(self, value):
        values = {
            "projid": "projid_4f419bd5258cd",
            "verb": "reserve",
            "lines" : [1000, 2000, 3000],
            "pageid" : "091",
            "text": "This is a yet another test"
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
        os.environ["REMOTE_ADDR"] = "127.0.0.1"
    else:
        cgitb.enable()
        form = cgi.FieldStorage()
    CommandProcessor(form).dispatch()



if __name__ == "__main__":
    main()

