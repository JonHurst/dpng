#!/usr/bin/python
# coding=utf-8

"""
Manages a "project" file which tracks the proofreading process.

The project file is a python pickle file, consisting of meta and project_data sections.

The meta section is a generic repository for things like titles, good words etc.

The project_data section is a dictionary relating a page_id to its relevant data. This data includes
the filenames of required image and text files and the list of lines in the image file.

"""

import os
import pickle
import hashlib
import datetime


DATA, STATUS, TIMESTAMP = range(3)

STATUS_NEW = 0X00
STATUS_DONE = 0X01
STATUS_USER = 0X10

class DataException(Exception):
    pass


class ProjectData:


    def __init__(self, project_file):
        self.project_file = project_file
        self.project_dir = os.path.dirname(project_file)
        if os.path.isfile(project_file):
            self.meta, self.project_data = pickle.load(open(self.project_file))
        else:
            self.meta = {}
            self.project_data = {}


    def save(self):
        pickle.dump((self.meta, self.project_data),
                    open(self.project_file, "w"))


    def get_meta(self, field):
        return self.meta.get(field)


    def set_meta(self, field, data):
        self.meta[field] = data


    def add_page(self, pageid, text, images):
        timestamp = datetime.datetime.utcnow()
        self.project_data[pageid] = {"images": [images, STATUS_NEW, timestamp],
                                     "lines": [None, STATUS_NEW, timestamp]}
        self.set_text(pageid, text)


    def exists(self, pageid, field=None):
        """Returns true if the page exists and the field exists, else returns false"""
        if (self.project_data.has_key(pageid) and
            (field == None or self.project_data[pageid].has_key(field))):
            return True
        return False


    def get_data(self, pageid, field):
        if not self.exists(pageid, field): raise DataException
        return self.project_data[pageid][field]


    def set_data(self, pageid, field, data, status=STATUS_NEW):
        if not self.exists(pageid): raise DataException
        if self.exists(pageid, field):
            status |= self.project_data[pageid][field][STATUS]
        self.project_data[pageid][field] = [data, status, datetime.datetime.utcnow()]


    def get_pages(self, field="ocr"):
        """Returns an alphabetically sorted list of tuples of the following form:
           (pageid, status, timestamp)
        """
        return [(X,
                 self.project_data[X][field][STATUS],
                 self.project_data[X][field][TIMESTAMP])
                for X in sorted(self.project_data.keys())
                if self.project_data[X].has_key(field)]


    def reserve(self, pageid, user):
        """Adds a field for USER to the page PAGEID"""
        if self.exists(pageid, user): return
        data = self.get_data(pageid, "ocr")
        self.set_data(pageid, user, data[DATA], STATUS_USER)


    def get_images(self, pageid):
        """Returns an object O for which:
           O[DATA]: (prior_image, image, next_image)
           O[STATUS]: status_code
           O[TIMESTAMP]: timestamp"""
        return self.get_data(pageid, "images")


    def get_lines(self, pageid):
        """Returns an object O for which:
           O[DATA]: (line_1, line_2, ...., line_n)
           O[STATUS]: status_code
           O[TIMESTAMP]: timestamp"""
        return self.get_data(pageid, "lines")


    def get_text(self, pageid, user=None):
        """Returns an object O for which:
           O[DATA]: filename of text
           O[STATUS]: status_code
           O[TIMESTAMP]: timestamp
           The text will be the last text submitted by the user for that page or,
           if no text has yet been submitted or the user is None, the OCR text"""
        if user and self.exists(pageid, user):
           text_data = self.get_data(pageid, user)
        else:
            text_data = self.get_data(pageid, "ocr")
        text_data[DATA] = open(os.path.join(self.project_dir, text_data[DATA])).read()
        return text_data


    def set_lines(self, pageid, lines, status=STATUS_NEW):
        """Set the lines for the page PAGEID. LINES must be a list of lines."""
        self.set_data(pageid, "lines", lines, status)


    def set_text(self, pageid, text, user=None):
        """Saves the text TEXT to a file and adds the filename to the project file. TEXT must
        be a simple stream of bytes, i.e. UTF-8 text should already be encoded."""
        if not self.exists(pageid): raise DataException
        h  = hashlib.sha1(text).hexdigest()
        target_file = os.path.join(self.project_dir, h)
        if not os.path.exists(target_file):
            open(target_file, "w").write(text)
            os.chmod(target_file, 0640)
        status = STATUS_DONE
        if user == None: user = "ocr"
        else: status |= STATUS_USER
        self.set_data(pageid, user, os.path.basename(target_file), status)
        #TODO: Need to have a reference counted hash of created filenames
        #so that we can unlink replaced files when there are no further
        #references..


    def dump(self):
        print self.meta
        print "\nPages:\n"
        for k in sorted(self.project_data.keys()):
            print k, ":"
            for l in sorted(self.project_data[k].keys()):
                print "  ", l, ":", self.project_data[k][l]
            print



