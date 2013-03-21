#!/usr/bin/python3

import argparse
import os
import sys
import xml.etree.ElementTree as et
import xml.etree.ElementInclude as ei
import project
import stat


def create_project(project_dir, rtt_file):
    rtt = et.parse(rtt_file).getroot()
    ei.include(rtt)
    data = project.ProjectData(project_dir)
    process_metadata(rtt, data)
    process_pages(rtt, data, project_dir)
    data.save()
    data.unlock()
    os.chmod(project_dir, 0o770 | stat.S_ISGID)
    os.chmod(project_dir + "/.lock", 0o660)
    os.chmod(project_dir + "/.project", 0o660)


def process_metadata(rtt, data):
    data.meta["title"] = rtt.find("title").text


def process_pages(rtt, data, project_dir):
    pages = rtt.findall("pages/page")
    idents = [p.attrib["id"] for p in pages]
    data.first_page = idents[0]
    for page, ident, prev_ident, next_ident in zip(pages, idents, [None] + idents[:-1], idents[1:] + [None]):
        proj_page = data.add_page(ident, prev_ident, next_ident)
        proj_page.add_image(os.path.abspath(page.find("image").attrib["src"]))
        proj_page.add_itext(page.find("text").text)
        lines = page.find("image/lines")
        if lines != None:
            proj_page.image_lines = [int(X) for X in lines.text.split(",")]


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
