#!/usr/bin/python

import sys
import os
import project_data
import xml.etree.ElementTree as et

def main():
    if (len(sys.argv) != 3 or
        not os.path.isfile(sys.argv[1]) or
        not os.path.isfile(sys.argv[2])):
        print "Usage: ", sys.argv[0], "project_file rtt_file"
        sys.exit(-1)
    pd = project_data.ProjectData(sys.argv[1])
    # pd.dump()
    et.register_namespace("xi", "http://www.w3.org/2001/XInclude")
    rtt = et.ElementTree(file=sys.argv[2])
    # et.dump(rtt.getroot())
    rtt_pages = rtt.findall(".//page")
    rtt_pages_dict = {}
    for p in rtt_pages:
        rtt_pages_dict[p.attrib["id"]] = p
    for (pageid, status, timestamp) in pd.get_pages():
        #look for pageid in rtt file
        l = pd.get_lines(pageid)
        p = rtt_pages_dict[pageid]
        i = p.find("image")
        le = i.find("lines")
        if le == None:
            le = et.SubElement(i, "lines")
        le.text = ",".join([str(X) for X in l[project_data.DATA]])
    rtt.write(sys.stdout, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    main()
