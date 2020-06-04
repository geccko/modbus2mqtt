#! /usr/bin/python3
#
# Strip superfluous commas and spaces from register file
# Libreoffice adds lots of commas to pad out to the number of columns
import sys
inputfile = open(sys.argv[1], "r")

while True:
    line = inputfile.readline()
    if not line:
        break
    output_line = line.rstrip().rstrip(',')
    print(output_line)

