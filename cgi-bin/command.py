#!/usr/bin/python
# coding=utf-8

import cgi
import cgitb
import sys
import json
import hashlib
import pickle
import os
import datetime
import xml.etree.cElementTree as et

data_path = "../data/"

class ProjectData:

    IMAGES, LINES, CURRENT, ALT = range(4)#format of page diary entries
    FILENAME, STATUS, TIMESTAMP = range(3)#format of alt file entries

    def __init__(self, project_file):
        if not os.path.exists(project_file):
            raise CommandException(CommandException.BADPROJECTFILE)
        self.project_file = project_file
        self.project_dir = os.path.dirname(project_file)
        self.load()


    def load(self):
        self.meta, self.project_data = pickle.load(open(self.project_file))


    def save(self):
        pickle.dump((self.meta, self.project_data),
                    open(self.project_file, "w"))


    def get_title(self):
        return self.meta["title"]


    def get_pages(self):
        return sorted(self.project_data.keys())


    def get_images(self, pageid):
        if pageid not in self.project_data.keys():
            raise CommandException(CommandException.BADPAGEID)
        return self.project_data[pageid][self.IMAGES]


    def get_lines(self, pageid):
        if pageid not in self.project_data.keys():
            raise CommandException(CommandException.BADPAGEID)
        return self.project_data[pageid][self.LINES]


    def set_lines(self, pageid, lines):
        if pageid not in self.project_data.keys():
            raise CommandException(CommandException.BADPAGEID)
        self.project_data[pageid][self.LINES] = lines
        self.save()


    def get_textdescriptor_field(self, pageid, user, field):
        if pageid not in self.project_data.keys():
            raise CommandException(CommandException.BADPAGEID)
        page_data = self.project_data[pageid]
        if user == None:
            return page_data[self.CURRENT][field]
        elif page_data[self.ALT].has_key(user):
            return page_data[self.ALT][user][field]
        else:
            return None


    def get_text(self, pageid, user=None):
        filename = self.get_textdescriptor_field(pageid, user, self.FILENAME)
        if not filename:
            filename = self.get_textdescriptor_field(pageid, None, self.FILENAME)
        return open(os.path.join(self.project_dir, filename)).read()


    def get_status(self, pageid, user=None):
        return self.get_textdescriptor_field(pageid, user, self.STATUS)


    def get_timestamp(self, pageid, user=None):
        return self.get_textdescriptor_field(pageid, user, self.TIMESTAMP)


    def post_text(self, pageid, user, text, status):
        if pageid not in self.project_data.keys():
            raise CommandException(CommandException.BADPAGEID)
        page_data = self.project_data[pageid]
        h  = hashlib.sha1(text).hexdigest()
        target_file = os.path.join(self.project_dir, h)
        if not os.path.exists(target_file):
            open(target_file, "w").write(text)
        old_data = page_data[self.ALT].get(user)
        page_data[self.ALT][user] = (h, status, datetime.datetime.utcnow())
        #now check whether we can unlink the file
        all_files = [page_data[self.ALT][X][self.FILENAME]
                     for X in page_data[self.ALT].keys()] + [page_data[self.CURRENT]]
        if old_data and old_data[self.FILENAME] not in all_files:
            os.unlink(os.path.join(self.project_dir, old_data[self.FILENAME]))
        self.save()


    def get_phase(self):
        return self.meta.get("phase")


    def set_phase(self, phase):
        self.meta["phase"] = phase




class CommandProcessor:


    def __init__(self, form, project_data):
        self.form = form
        self.data = project_data
        self.func_map = {
            "get": self.get,
            "list": self.list_pages,
            "save": self.save,
            "lines": self.update_lines
            }


    def dispatch(self):
        verb = self.form.getfirst("verb")
        if not verb: raise CommandException(CommandException.NOVERB)
        if  verb not in self.func_map.keys():
            raise CommandException(CommandException.UNKNOWNVERB)
        self.func_map[verb]()


    def list_pages(self):
        pages = self.data.get_pages()
        available, done = [], []
        for p in pages:
            status = self.data.get_status(p, os.environ["REMOTE_ADDR"])
            timestamp = self.data.get_timestamp(p, os.environ["REMOTE_ADDR"])
            if not timestamp:
                timestamp = self.data.get_timestamp(p)
            table = done if status else available
            table.append(
                ("<tr>"
                 "<td><a href='%(pageid)s'>%(pageid)s</a></td>"
                 "<td>%(timestamp)s</td>"
                 "</tr>" % {"pageid": p, "timestamp": timestamp.strftime("%Y-%m-%d %H:%M")}))
        template = "<h1>%s</h1><table>%s</table>"
        available = template % ("Available", "".join(available)) if available else ""
        done = template % ("Done", "".join(done)) if done else ""
        print "Content-type: text/html; charset=UTF-8\n"
        print "<div id='pagepicker_tables'>", available, done, "</div>"


    def get(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        print "Content-type: application/json; charset=UTF-8\n"
        json.dump([pageid, self.data.get_title(), self.data.get_text(pageid, os.environ["REMOTE_ADDR"]),
                   self.data.get_images(pageid), self.data.get_lines(pageid)], sys.stdout)


    def save(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        text = self.form.getfirst("text")
        if not text: text = ""
        if len(text) > 10240: raise CommandException(CommandException.TOOLARGETEXT)
        self.data.post_text(pageid, os.environ["REMOTE_ADDR"], text, 1)
        print "Content-type: application/json; charset=UTF-8\n"
        json.dump("OK", sys.stdout)


    def update_lines(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise CommandException(CommandException.NOPAGEID)
        lines = self.form.getfirst("lines")
        if not lines:  raise CommandException(CommandException.NOLINES)
        lines = json.loads(lines)
        self.data.set_lines(pageid, lines)
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
            "verb": "lines",
            "lines" : [1000, 2000, 3000],
            "pageid" : "092.png",
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
        os.environ["REMOTE_ADDR"] = "127.0.0.2"
    else:
        cgitb.enable()
        form = cgi.FieldStorage()
    os.environ["REMOTE_ADDR"] = "127.0.0.2" #debug
    projid = form.getfirst("projid")
    if not projid: raise CommandException(CommandException.NOPROJID)
    pd = ProjectData(os.path.join(data_path, projid, "project"))
    CommandProcessor(form, pd).dispatch()



if __name__ == "__main__":
    main()

