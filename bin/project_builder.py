#!/usr/bin/python

"""Takes a directory with text files, downloads matching images, and
runs a line scan on them to create line files. Then a project file is
pickled from all the data so that it can be used by command.py"""


import sys
import glob
import urllib
import os
import linedetect
import json
import hashlib
import pickle
import datetime

image_url_template = "http://www.pgdp.net/projects/%s/%s" #(projectid, pngname)

def scan_directory(directory):
    filenames = glob.glob(os.path.join(directory, "*.txt"))
    files = [os.path.abspath(X) for X in filenames]
    files.sort()
    return files


def download_image(projectid, image, imagepath):
    urllib.urlretrieve(image_url_template % (projectid, image), imagepath)


def make_first_text(raw_file, encoding):
    data = unicode(open(raw_file).read(), encoding)
    output_lines = []
    for line in data.splitlines():
        output_lines.append(line.rstrip())
    output_data = "\n".join(output_lines).encode("utf-8")
    filename = os.path.join(os.path.dirname(raw_file),
                            hashlib.sha1(output_data).hexdigest())
    open(filename, "w").write(output_data)
    os.chmod(filename, 0640)
    return os.path.basename(filename)



if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "Usage: %s project_id project_dir title [encoding]" % sys.argv[0]
        sys.exit(-1)
    project_id = sys.argv[1]
    project_dir = sys.argv[2]
    title = sys.argv[3]
    encoding = "latin1"
    data_path = os.path.abspath(project_dir)
    while True:
        head, tail = os.path.split(data_path)
        if tail == "data": break
        if not head:
            print "No parent directory named 'data' found"
            sys.exit(-1)
        data_path = head
    if len(sys.argv) == 5:
        encoding = sys.argv[4]
    if not os.path.isdir(project_dir):
        print project_dir, "is not a directory"
        sys.exit(-1)
    text_files = scan_directory(sys.argv[2])
    text_list, image_list, lines_list = [], [], []
    for f in text_files:
        text_list.append([make_first_text(f, encoding), 0, datetime.datetime.utcnow()])
        image_path = f[:-3] + "png"
        image = os.path.basename(image_path)
        if os.path.exists(image_path):
            print image_path, "exists"
        else:
            print "Downloading", image, "to",  image_path
            download_image(sys.argv[1], image, image_path)
            os.chmod(image_path, 0640)
        image = os.path.relpath(image_path, data_path)
        image_list.append(image)
        lines_list.append(linedetect.process_image(image_path, 16))
    context_image_list = zip([None] + image_list[:-1], image_list, image_list[1:] + [None])
    alt_list = [{} for X in image_list]
    page_ids = [os.path.basename(X).replace(".png", "")  for X in image_list]
    output = zip(context_image_list, lines_list, text_list, alt_list)
    output = [list(X) for X in output]
    output = dict(zip(page_ids, output))
    project_filename = os.path.join(project_dir, "project")
    project = open(project_filename, "w")
    pickle.dump(({"id": project_id, "title": title, "phase": "lines"}, output), project)
    os.chmod(project_filename, 0660)



