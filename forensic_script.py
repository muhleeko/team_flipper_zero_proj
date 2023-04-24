#!/usr/bin/env python
'''
Copyright (C) 2013 Kevin Breen.
Python script to MNT Partitions on a Disk Image
http://techanarchy.net
'''
__description__ = 'Python script to MNT Partitions on a Disk Image'
__author__ = 'Kevin Breen @KevTheHermit'
__version__ = '0.5'
__date__ = '2014/09/13'

# https://stackoverflow.com/questions/11344557/replacement-for-getstatusoutput-in-python-3

import os
import sys
import hashlib
# import commands depricated
import subprocess
from datetime import datetime
from optparse import OptionParser, OptionGroup

supported_types = ['0x83', '0x07', '0x0b', '0x0c','0x06', '0x17', '0x16', '0x1b', '0x1c', 'Basic data partition']
vfat = ['0x0b', '0x0c', '0x06', '0x1b', '0x1c', '0x16']
ntfs = ['0x07', '0x17', 'Basic data partition']


def parse_mmls(img_path):
    # use mmls to get a list of partitions.
    md5sum_output = subprocess.getoutput("md5sum {0}".format(img_path))
    print("The MD5 hash is: ")
    print(md5sum_output)
    print("")
    try:
        mmls_output = subprocess.getoutput("mmls {0}".format(img_path))
    except Exception as e:
        print("[+] MMLS Failed with Exception {0}".format(e))
        return False, False
    #Build a Dictionary containing all the Partition Information
    print("MMLS OUTPUT BELOW")
    print(mmls_output)
    partition_info = {}
    part_count = 0
    for line in mmls_output.split('\n'):
        if line == 'Cannot determine partition type':
            print("[+] Image file doesnt Contain a Partition Table")
            print("[+] If this is a single partition try the '-s' option")
            sys.exit()
        # We need sector size.
        if line.startswith('Units'):
            sector_size = int(line.split()[3].split('-')[0])
        # we need to get all the partitions. But only supported ones
        if any(fs_type in line for fs_type in supported_types):
            # Dict for single part
            inf = {}
            line_info = line.split('   ')
            if len(line_info) == 5:
                inf['Start'] = int(line_info[1])
                inf['End'] = int(line_info[2])
                inf['Length'] = int(line_info[3])
                inf['Type'] = line_info[4].split('(')[1][:-1]
            elif len(line_info) == 6:
                inf['Start'] = int(line_info[2])
                inf['End'] = int(line_info[3])
                inf['Length'] = int(line_info[4])
                inf['Type'] = line_info[5]
            # Calculated offset
            inf['Offset'] = inf['Start'] * sector_size
            # add partition to list of all parts
            partition_info[part_count] = inf
            part_count += 1
            print(partition_info)
            #print(part_count)
    return partition_info, part_count

if __name__ == "__main__":
    parse_mmls("/Users/leeko/Desktop/proj_flip/flip.dd")