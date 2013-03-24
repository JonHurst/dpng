#!/usr/bin/python3

import cgi
import cgitb
import sys
import os
import command
import project
import json
import linedetect


class LineCommandProcessor(command.CommandProcessor):

    def __init__(self, form):
        command.CommandProcessor.__init__(self, form)
        self.rw_func_map["save_lines"] = self.save_lines
        self.ro_func_map["calc_lines"] = self.calc_lines
        self.ro_func_map["list_lines"] = self.list_lines


    def save_lines(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise command.CommandException(CommandException.NOPAGEID)
        lines = self.form.getfirst("lines")
        if lines:
            lines = json.loads(lines)
        self.data.pages[pageid].lines = lines
        self.data.save()
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump("OK", sys.stdout)


    def calc_lines(self):
        pageid = self.form.getfirst("pageid")
        if not pageid: raise command.CommandException(CommandException.NOPAGEID)
        page = self.data.pages[pageid]
        image_file = os.path.join(page.base_dir, page.image_filename)
        lines = linedetect.process_image(image_file, 16)
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump([int(X) for X in lines], sys.stdout)


    def list_lines(self):
        todo, done = [], []
        ident = self.data.first_page
        while ident != None:
            page = self.data.pages[ident]
            if page.image_lines:
                done.append(ident)
            else:
                todo.append(ident)
            ident = self.data.pages[ident].next_ident
        print("Content-type: text/json; charset=UTF-8\n")
        json.dump((todo, done), sys.stdout)



##############################
#fake environment for testing.
#Comment out in final
class FakeForm:
    def getfirst(self, value):
        values = {
            "projid": "test",
            "verb": "list_lines",
            "pageid": "001"
            }
        return values.get(value)
#
##############################

def main():
    if  "test" in sys.argv:
        form = FakeForm()
        os.environ["REMOTE_ADDR"] = "127.0.0.1"
        # os.environ["REMOTE_USER"] = "jon"
    else:
        cgitb.enable()
        form = cgi.FieldStorage()
    LineCommandProcessor(form).dispatch()



if __name__ == "__main__":
    main()

