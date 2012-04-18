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
import fcntl
import random


DATA, STATUS, TIMESTAMP = range(3)

STATUS_NEW = 0X00
STATUS_DONE = 0X01
STATUS_USER = 0X10

class DataException(Exception):
    pass


class ProjectData:


    def __init__(self, project_file, write=False):
        self.project_file = project_file
        self.project_dir = os.path.dirname(project_file)
        self.lock = fcntl.LOCK_EX if write else fcntl.LOCK_SH
        if os.path.exists(self.project_file):
            self.project_file = open(project_file, "rb+")
        else:
            self.project_file = open(project_file, "wb+")
        fcntl.lockf(self.project_file, self.lock)
        pickle_string = self.project_file.read()
        if pickle_string:
            self.meta, self.project_data = pickle.loads(pickle_string)
        else:
            self.meta = {}
            self.project_data = {}


    def __del__(self):
        self.unlock()


    def save(self):
        if self.lock != fcntl.LOCK_EX or not self.project_file: raise DataException
        self.project_file.seek(0)
        self.project_file.truncate()
        pickle.dump((self.meta, self.project_data), self.project_file)
        self.project_file.flush()
        self.unlock()
        self.project_file = None


    def unlock(self):
        if self.lock != fcntl.LOCK_UN:
            fcntl.lockf(self.project_file, fcntl.LOCK_UN)
        self.lock = fcntl.LOCK_UN


    def get_meta(self, field):
        return self.meta.get(field)


    def set_meta(self, field, data):
        self.meta[field] = data


    def add_page(self, pageid, text, images):
        timestamp = datetime.datetime.utcnow()
        self.project_data[pageid] = {"images": [images, STATUS_NEW, timestamp],
                                     "lines": [None, STATUS_NEW, timestamp]}
        self.set_text(pageid, text, "ocr")


    def exists(self, pageid, field=None):
        """Returns true if the page exists and the field exists, else returns false"""
        if (self.project_data.has_key(pageid) and
            (field == None or self.project_data[pageid].has_key(field))):
            return True
        return False


    def is_done(self, pageid, field):
        """Returns True if the page exists and is STATUS_DONE for field"""
        if self.exists(pageid, field) and (self.project_data[pageid][field][STATUS] & STATUS_DONE):
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


    def rm_data(self, pageid, field):
        if not self.exists(pageid): raise DataException
        if self.exists(pageid, field):
            del self.project_data[pageid][field]


    def get_pages(self, field="images"):
        """Returns an alphabetically sorted list of tuples of the following form:
           (pageid, status, timestamp)
        """
        return [(X,
                 self.project_data[X][field][STATUS],
                 self.project_data[X][field][TIMESTAMP])
                for X in sorted(self.project_data.keys())
                if self.project_data[X].has_key(field)]


    def reserve(self, pageid, user, source):
        """Adds a field for USER to the page PAGEID"""
        if self.exists(pageid, user): return
        data = self.get_data(pageid, source)
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


    def get_text(self, pageid, user):
        """Returns an object O for which:
           O[DATA]: filename of text
           O[STATUS]: status_code
           O[TIMESTAMP]: timestamp
           The text will be the last text submitted by the user for that page or,
           the text copied during the reservation process. Returns None if the text
           does not exist"""
        text_data = None
        if user and self.exists(pageid, user):
           text_data = self.get_data(pageid, user)
           #replace filename with actual text
           text_data[DATA] = open(os.path.join(self.project_dir, text_data[DATA])).read()
        return text_data


    def set_lines(self, pageid, lines, status=STATUS_NEW):
        """Set the lines for the page PAGEID. LINES must be a list of lines."""
        self.set_data(pageid, "lines", lines, status)


    def set_text(self, pageid, text, user=None, done=True):
        """Saves the text TEXT to a file and adds the filename to the project file. TEXT must
        be a simple stream of bytes, i.e. UTF-8 text should already be encoded."""
        if not self.exists(pageid): raise DataException
        h = hashlib.sha1(text).hexdigest()
        target_file = os.path.join(self.project_dir, h)
        if not os.path.exists(target_file):
            temp_target = target_file + str(random.getrandbits(16))
            open(temp_target, "w").write(text)
            os.rename(temp_target, target_file)#rename is a POSIX atomic operation
            os.chmod(target_file, 0640)
        status = STATUS_DONE if done else STATUS_NEW
        if user == None: user = "ocr"
        else: status |= STATUS_USER
        self.set_data(pageid, user, os.path.basename(target_file), status)
        #TODO: Need to have a reference counted hash of created filenames
        #so that we can unlink replaced files when there are no further
        #references..


    def quality(self, pageid, prefix):
        """Returns a tuple of two numbers of the form (ACTUAL_QUALITY, PROJECTED_QUALITY) for PAGEID based on
        blocks with keys starting with PREFIX"""
        if not self.exists(pageid): raise DataException
        page = self.project_data[pageid]
        all_fields = [X for X in page.keys() if X.startswith(prefix)]
        done_fields = [X for X in all_fields if page[X][STATUS] & STATUS_DONE]
        return (len(done_fields), len(all_fields))


    def dump(self, only_done=False):
        print self.meta
        print "\nPages:\n"
        for k in sorted(self.project_data.keys()):
            print k, ":"
            for l in sorted(self.project_data[k].keys()):
                if only_done and not self.project_data[k][l][STATUS] & STATUS_DONE: continue
                print "  ", l, ":", self.project_data[k][l]
            print "Proof quality", self.quality(k, "proof/")
            print



