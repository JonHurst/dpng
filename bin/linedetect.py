#!/usr/bin/python

import sys
import scanner


def process_image(img, sample_fraction):
    pure_white_threshold = 0.95 #pure white is excluded from centile calculation
    white_threshold_factor = 0.7
    black_threshold_factor = 0.5
    min_line_size = 6
    rows = scanner.process_image(img, sample_fraction)
    #note row[0] will always be pure white
    #find 10th centile value
    sortedrows = [ X for X in rows if X < rows[0] * pure_white_threshold]
    sortedrows.sort()
    if not sortedrows: return []
    centile10 = sortedrows[len(sortedrows) / 10]
    white_threshold = centile10 + (rows[0] - centile10) * (white_threshold_factor)
    black_threshold = centile10 + (rows[0] - centile10) * (black_threshold_factor)
    #white eats gray
    #first top to bottom
    white = True
    for c in range(0, len(rows)):
        if rows[c] > white_threshold:
            white = True
        elif rows[c] < black_threshold:
            white = False
        else: #gray
            if white: rows[c] = rows[0]
    #now bottom to top
    white = True
    for c in range(len(rows), 0, -1):
        if rows[c - 1] > white_threshold:
            white = True
        elif rows[c - 1] < black_threshold:
            white = False
        else: #gray
            if white:
                rows[c - 1] = rows[0]
            else:
                rows[c - 1] = int(black_threshold) - 1
    #calculate line centers
    lines = []
    white = True
    for c, row in enumerate(rows):
        if row > black_threshold:
            white = True
        else:
            if white:
                lines.append([c, 0])
                white = False;
            lines[-1][1] += 1
    # for l in lines:
    #     if l[1] < min_line_size: continue
    #     line = l[0] + l[1] / 2
    return [ (X[0] + X[1]/2) * 10000/len(rows) for X in lines if X[1] >= min_line_size ]


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1][0] == "-":
        print "Usage: %s png_file sample_fraction" % sys.argv[0]
        sys.exit(-1)
    print process_image(sys.argv[1], int(sys.argv[2]))
