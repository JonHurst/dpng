#!/usr/bin/python
# coding=utf-8

import os
import pickle
import hashlib
import datetime


class DataException(Exception):
    pass


class ProjectData:

    IMAGES, LINES, CURRENT, ALT = range(4)#format of page diary entries
    FILENAME, STATUS, TIMESTAMP = range(3)#format of alt file entries

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
        # os.chmod(self.project_file, 0660)



    def get_meta(self, field):
        return self.meta[field]


    def set_meta(self, field, data):
        self.meta[field] = data


    def add_page(self, pageid, text, images):
        self.project_data[pageid] = [images, None, [text, 0, datetime.datetime.utcnow()], {}]


    def get_pages(self):
        return sorted(self.project_data.keys())


    def get_images(self, pageid):
        if pageid not in self.project_data.keys():
            raise DataException
        return self.project_data[pageid][self.IMAGES]


    def get_lines(self, pageid):
        if pageid not in self.project_data.keys():
            raise DataException
        return self.project_data[pageid][self.LINES]


    def set_lines(self, pageid, lines):
        if pageid not in self.project_data.keys():
            raise DataException
        self.project_data[pageid][self.LINES] = lines
        self.save()


    def get_textdescriptor_field(self, pageid, user, field):
        if pageid not in self.project_data.keys():
            raise DataException
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
            raise DataException
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


    def dump(self):
        print self.meta
        print "\nPages:\n"
        for k in sorted(self.project_data.keys()):
            print k, self.project_data[k]


