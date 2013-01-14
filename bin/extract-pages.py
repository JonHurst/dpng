#!/usr/bin/python

import sys
import os
import re
import project_data

def main():
    if (len(sys.argv) != 3 or
        not os.access(sys.argv[1], os.R_OK) or
        not os.path.isdir(sys.argv[2])):
        print "Usage: %s project_file output_directory" % sys.argv[0]
        sys.exit(-1)
    pd = project_data.ProjectData(sys.argv[1])
    pages = [X[0] for X in pd.get_pages("proof/127.0.0.1")]
    for p in pages:
        outfile = open(sys.argv[2] + "/" + p, "w")
        outfile.write(pd.get_text(p, "proof/127.0.0.1")[project_data.DATA] + "\n")
        outfile.close()


if __name__ == "__main__":
    main()
