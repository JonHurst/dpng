#!/usr/bin/python2.7
from __future__ import print_function

import argparse
import os
import sys
import xml.etree.ElementTree as et
import xml.etree.ElementInclude as ei
import project_data


def create_project(project_dir, rtt_file):
    project_file = project_dir + "/project"
    data = project_data.ProjectData(project_file, True)
    rtt = et.parse(rtt_file).getroot()
    ei.include(rtt)
    process_metadata(rtt, data)
    process_pages(rtt, data, project_dir)
    data.save() #also unlocks
    os.chmod(project_file, 0660)


def process_metadata(rtt, data):
    data.set_meta("title", rtt.find("title").text)


def process_pages(rtt, data, project_dir):
    pages = rtt.findall("pages/page")
    images = []
    for p in pages:
        page_image = p.find("image").attrib["src"]
        proj_image = os.path.join(project_dir, os.path.basename(page_image))
        if not os.path.exists(proj_image):
            os.link(page_image, proj_image)
            os.chmod(proj_image, 0640)
        images.append(os.path.basename(proj_image))
    for p, pi, i, ni in zip(pages, [None] + images[:-1], images, images[1:] + [None]):
        data.add_page(p.attrib["id"], p.find("text").text.encode("utf-8"), [pi, i, ni])
        lines = p.find("image/lines")
        if lines != None:
            data.set_lines(p.attrib["id"], [int(X) for X in lines.text.split(",")])


def main():
    parser = argparse.ArgumentParser(description="Create project from RTT file")
    parser.add_argument("rtt_file", help="RTT file")
    parser.add_argument("project_dir", help="Project directory")
    args = parser.parse_args()
    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print("Error: ", project_dir, "is not a directory\n", file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(-1)
    rtt_file = os.path.abspath(args.rtt_file)
    if not os.path.isfile(rtt_file):
        print("Error:", rtt_file, "is not a file\n", file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(-2)
    os.chdir(os.path.dirname(rtt_file))
    create_project(project_dir, rtt_file)


if __name__ == "__main__":
    main()
