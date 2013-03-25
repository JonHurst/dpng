#!/usr/bin/python3

import sys
import scanner
import math


def thresholds(img, sample_fraction):
    rows = scanner.process_image(img, sample_fraction)
    s = sum(rows)
    ssq = sum([X*X for X in rows])
    avg = s / len(rows)
    var = (ssq / len(rows)) - avg * avg
    sdev = math.sqrt(var)
    white_threshold = avg + 0.6 * sdev
    black_threshold = avg - 0.4 * sdev
    return (int(black_threshold * 100 / rows[0]),
            int(white_threshold * 100 / rows[0]))


def process_image(img, sample_fraction=32, black_threshold=55, white_threshold=85):
    rows = scanner.process_image(img, sample_fraction)
    min_line_size = len(rows) / 300
    white_threshold = int(white_threshold) * rows[0] / 100
    black_threshold = int(black_threshold) * rows[0] / 100
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
    return [ (X[0] + X[1]/2) * 10000/len(rows) for X in lines if X[1] >= min_line_size ]


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1][0] == "-":
        print("Usage: %s png_file sample_fraction" % sys.argv[0])
        sys.exit(-1)
    print(process_image(sys.argv[1], int(sys.argv[2])))
