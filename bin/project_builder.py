#!/usr/bin/python

"""Takes a directory with text files, downloads matching images, and
runs a line scan on them to create line files. Then a project file is
pickled from all the data so that it can be used by command.py"""


import sys
import glob
import urllib
import os
import linedetect
import optparse
import project_data
import re


class BuilderException(Exception):
    (BAD_DIRECTORY, BAD_PROJECT_FILE) = range(2)
    def __init__(self, code):
        self.code = code


class ProjectBuilder:

    re_tws = re.compile(r"[^\S\n]+\n", re.UNICODE)

    def __init__(self, options):
        self.proj_dir = options.directory or os.getcwd()
        if not os.path.isdir(self.proj_dir): raise BuilderException(BuilderException.BAD_DIRECTORY)
        self.options = options
        self.project_file = os.path.join(self.proj_dir, "project")


    def build(self):
        filenames = glob.glob(os.path.join(self.proj_dir, "*.txt"))
        files = [os.path.abspath(X) for X in filenames]
        files.sort()
        images = [os.path.basename(X[:-3] + "png") for X in files]
        context_images = zip([None] + images[:-1], images, images[1:] + [None])
        encoding = self.options.encoding or "utf-8"
        data = project_data.ProjectData(self.project_file, True)
        data.set_meta("title", self.options.title or os.path.basename(self.proj_dir))
        for c, f in enumerate(files):
            pageid = os.path.basename(f)[:-4]
            if data.exists(pageid) and not self.options.overwrite: continue
            text = unicode(open(f).read(), encoding)
            text = self.re_tws.sub(r"\n", text).rstrip() #strip trailing EOL and EOS whitespace
            data.add_page(pageid,
                          text.encode("utf-8"),
                          context_images[c])
        data.save() #also unlocks
        os.chmod(self.project_file, 0660)


    def lines(self):
        skiplines = self.options.skiplines or 0
        data = project_data.ProjectData(self.project_file, True)
        pages = [X[0] for X in data.get_pages()]
        for p in pages:
            image = data.get_images(p)[project_data.DATA][1]
            if self.options.overwrite or data.get_lines(p)[project_data.DATA] == None:
                imagepath = os.path.join(self.proj_dir, image)
                lines = linedetect.process_image(imagepath, 16)
                data.set_lines(p, lines[skiplines:])
        data.save() #also unlocks


    def images(self):
        baseurl = self.options.img_url or "http://www.pgdp.net/projects/%s/" % os.path.basename(self.proj_dir)
        pages = [X[0] for X in self.data.get_pages()]
        data = project_data.ProjectData(self.project_file)
        for p in pages:
            image = data.get_images(p)[project_data.DATA][1]
            imagepath = os.path.join(self.proj_dir, image)
            if os.path.exists(imagepath):
                print imagepath, "exists"
            else:
                print "Downloading", baseurl + "/" + image, "to", imagepath
                urllib.urlretrieve(baseurl + "/" + image, imagepath)
                os.chmod(imagepath, 0640)
        data.unlock()


    def add_goodwords(self):
        data = project_data.ProjectData(self.project_file, True)
        data.set_meta("goodwords",
                      ";".join([unicode(X, "utf-8").rstrip().encode("utf-8")
                                for X in open(os.path.join(self.proj_dir, "goodwords")).readlines()]))
        data.save() #also unlocks


    def dump(self):
        data = project_data.ProjectData(self.project_file)
        data.dump(self.options.processed)
        data.unlock()


def main():
    usage = "usage: %prog [build|lines|goodwords|images|dump] [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-e", "--encoding", dest="encoding",
                      help="The encoding of the source text files")
    parser.add_option("-d", "--directory", dest="directory",
                      help="The directory to process, if it is not CWD")
    parser.add_option("-u", "--url", dest="img_url",
                      help="Base URL to download images from (uses CWD if omitted")
    parser.add_option("-t", "--title", dest="title",
                      help="Project title.")
    parser.add_option("-s", "--skiplines", dest="skiplines", type="int",
                      help="Lines to skip when processing lines (for running headers)")
    parser.add_option("-o", "--overwrite", dest="overwrite", action="store_true",
                      help="Overwrite exisitng data")
    parser.add_option("-p", "--processed", dest="processed", action="store_true",
                      help="Only include blocks with STATUS_DONE flag set when dumping")
    (options, args) = parser.parse_args()
    pb = ProjectBuilder(options)
    command = args[0] if len(args) else None
    if command == "build":
        pb.build()
    elif command == "lines":
        pb.lines()
    elif command == "images":
        pb.images()
    elif command == "dump":
        pb.dump()
    elif command == "goodwords":
        pb.add_goodwords()
    else:
        parser.print_help()



if __name__ == "__main__":
    main()

