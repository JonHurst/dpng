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
import hashlib



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
        self.data = project_data.ProjectData(os.path.join(self.proj_dir, "project"))
        self.data.set_data_dir(options.datadir or
                              "/" + os.path.relpath(self.proj_dir, os.path.join(self.proj_dir, "../..")))


    def _create_text_file(self, filename, encoding):
        data = unicode(open(filename).read(), encoding)
        data = self.re_tws.sub(r"\n", data) #strip trailing EOL whitespace
        data = data.rstrip() #strip EOS whitespace
        filename = os.path.join(self.proj_dir, hashlib.sha1(data.encode("utf-8")).hexdigest())
        open(filename, "w").write(data.encode("utf-8"))
        os.chmod(filename, 0640)
        return filename


    def build(self):
        filenames = glob.glob(os.path.join(self.proj_dir, "*.txt"))
        files = [os.path.abspath(X) for X in filenames]
        files.sort()
        images = [os.path.basename(X[:-3] + "png") for X in files]
        self.data.set_title(options.title or os.path.basename(self.proj_dir))
        context_images = zip([None] + images[:-1], images, images[1:] + [None])
        encoding = self.options.encoding or "utf-8"
        for c, f in enumerate(files):
            self.data.add_page(os.path.basename(f)[:-4],
                               os.path.basename(self._create_text_file(f, encoding)),
                               context_images[c])
        self.data.save()


    def lines(self):
        pages = self.data.get_pages()
        skiplines = self.options.skiplines or 0
        for p in pages:
            image = self.data.get_images(p)[1]
            print image
            if self.options.overwrite or self.data.get_lines(p) == None:
                imagepath = os.path.join(self.proj_dir, image)
                print imagepath
                lines = linedetect.process_image(imagepath, 16)
                print lines
                self.data.set_lines(p, lines[skiplines:])


    def images(self):
        baseurl = self.options.img_url or "http://www.pgdp.net/projects/%s/" % os.path.basename(self.proj_dir)
        pages = self.data.get_pages()
        for p in pages:
            image = self.data.get_images(p)[1]
            imagepath = os.path.join(self.proj_dir, image)
            if os.path.exists(imagepath):
                print imagepath, "exists"
            else:
                print "Downloading", baseurl + "/" + image, "to", imagepath
                urllib.urlretrieve(baseurl + "/" + image, imagepath)
                os.chmod(imagepath, 0640)



def main():
    usage = "usage: %prog [build|lines|images|dump] [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-e", "--encoding", dest="encoding",
                      help="The encoding of the source text files")
    parser.add_option("-d", "--directory", dest="directory",
                      help="The directory to process, if it is not CWD")
    parser.add_option("-u", "--url", dest="img_url",
                      help="Base URL to download images from (uses CWD if omitted")
    parser.add_option("-t", "--title", dest="title",
                      help="Project title.")
    parser.add_option("-r", "--datadir", dest="datadir",
                      help="The path to the directory containing the data from the web server's perspective")
    parser.add_option("-s", "--skiplines", dest="skiplines", type="int",
                      help="Lines to skip when processing lines (for running headers)")
    parser.add_option("-o", "--overwrite", dest="overwrite", action="store_true",
                      help="Overwrite exisitng data")
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
        pb.data.dump()
    else:
        parser.print_help()



if __name__ == "__main__":
    main()

