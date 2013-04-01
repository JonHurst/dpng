#!/usr/bin/python3

import argparse
import os
import sys
import project


def main():
    parser = argparse.ArgumentParser(description="Manage metadata in project file")
    parser.add_argument("verb", help="add")
    parser.add_argument("project_dir", help="Project directory")
    parser.add_argument("key", help="Metadata key")
    parser.add_argument("value", help="Metadata value")
    args = parser.parse_args()
    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print("Error: ", project_dir, "is not a directory\n", file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(-1)
    data = project.ProjectData(project_dir)
    data.meta[args.key] = args.value
    data.save()
    data.unlock()



if __name__ == "__main__":
    main()
