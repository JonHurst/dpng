#!/usr/bin/python

import cgi
import cgitb
import sys

##############################
#fake environment for testing.
#Comment out in final
class FakeForm:
    def getfirst(self, value):
        values = {
            "projid": "projid_4f419bd5258cd",
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
    else:
        cgitb.enable()
        form = cgi.FieldStorage()
    print "Content-type: text/html; charset=UTF-8\n"
    template = unicode(file("../proof/proofreading_control.html").read(), "utf-8")
    print template.replace("projid", form.getfirst("projid")).encode("utf-8")


if __name__ == "__main__":
    main()
