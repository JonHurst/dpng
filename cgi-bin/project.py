#!/usr/bin/python3

import os
import sys
import hashlib
import random
import datetime
import fcntl
import pickle


class ProjectData:

    def __init__(self, project_dir, readonly=False):
        self.lock = fcntl.LOCK_SH if readonly else fcntl.LOCK_EX
        self.lf = open(project_dir + "/.lock", "wb+")
        fcntl.lockf(self.lf, self.lock)
        self.project_dir = project_dir
        self._pickle_filename = project_dir + "/.project"
        if os.path.exists(self._pickle_filename):
            self.meta, self.first_page, self.pages = pickle.loads(open(self._pickle_filename, "rb").read())
        else:
            self.meta = {}
            self.pages = {}
            self.first_page = None


    def add_page(self, ident, prev_ident, next_ident):
        page = Page(prev_ident, next_ident, self.project_dir)
        self.pages[ident] = page
        return page


    def unlock(self):
        if self.lock == fcntl.LOCK_UN: return
        self.lock = fcntl.LOCK_UN
        fcntl.lockf(self.lf, fcntl.LOCK_UN)
        self.lf.close()


    def save(self):
        assert self.lock == fcntl.LOCK_EX
        pickle_file = open(self._pickle_filename, "wb")
        pickle.dump((self.meta, self.first_page, self.pages), pickle_file)
        pickle_file.close()


    def dump(self):
        for k in self.meta:
            print(k, ": ", self.meta[k])
        ident = self.first_page
        while ident != None:
            print("\n", ident)
            page = self.pages[ident]
            print("  ", "image:", page.image_filename)
            print("  ", "itext:", page.itext_filename)
            print("  ", "otext:")
            for u in sorted(page.otext_filenames):
                print("    ", u, page.otext_filenames[u])
            if page.image_lines != None:
                print("  ", "lines", page.image_lines)
            ident = page.next_ident


class Page:

    def __init__(self, prev_ident, next_ident, base_dir):
        self.prev_ident = prev_ident
        self.next_ident = next_ident
        self.base_dir = base_dir
        self.image_filename = None
        self.image_lines = None
        self.itext_filename = None
        self.otext_filenames = {}
        self.otext_timestamps = {}


    def add_image(self, image_filename):
        proj_image = os.path.join(self.base_dir, os.path.basename(image_filename))
        if not os.path.exists(proj_image):
            os.link(image_filename, proj_image)#hard link is a POSIX atomic operation
            os.chmod(proj_image, 0o640)
        self.image_filename = os.path.basename(proj_image)


    def add_itext(self, text):
        self.itext_filename = self._create_text_file(text)


    def add_otext(self, text, user_id):
        if text == None:
            self.otext_filenames[user_id] = None
        else:
            self.otext_filenames[user_id] = self._create_text_file(text)
        self.otext_timestamps[user_id] = datetime.datetime.utcnow()


    def get_image(self):
        return open(os.path.join(self.base_dir, self.image_filename), "rb").read()


    def get_text(self, user_id):
        ofilename = self.otext_filenames.get(user_id)
        if ofilename:
            return open(os.path.join(self.base_dir, self.otext_filenames[user_id]), encoding="utf-8").read()
        else:
            return open(os.path.join(self.base_dir, self.itext_filename), encoding="utf-8").read()


    def _create_text_file(self, text):
        h = hashlib.sha1(bytes(text, encoding="utf-8")).hexdigest()
        target_file = os.path.join(self.base_dir, h)
        if not os.path.exists(target_file):
            temp_target = target_file + str(random.getrandbits(16))
            open(temp_target, "w", encoding="utf-8").write(text)
            os.rename(temp_target, target_file)#rename is a POSIX atomic operation
            os.chmod(target_file, 0o640)
        return h


if __name__ == "__main__":
    p = ProjectData(sys.argv[1])
    p.unlock()
    p.dump()
