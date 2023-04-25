#!/usr/bin/env python
'''
Python script to perform analysis on Disk Image by creating partions and recoverying deleted files
'''
__description__ = 'Python script to carve and analyze Partitions on a Disk Image'
__author__ = 'Muhleeko'
__version__ = '0.2'
__date__ = '25 APR 2023'

# https://stackoverflow.com/questions/11344557/replacement-for-getstatusoutput-in-python-3

import os
import sys
import hashlib
import getopt
# import commands depricated
import subprocess
from datetime import datetime
from optparse import OptionParser, OptionGroup

supported_types = ['0x83', '0x07', '0x0b', '0x0c','0x06', '0x17', '0x16', '0x1b', '0x1c', 'Basic data partition']
vfat = ['0x0b', '0x0c', '0x06', '0x1b', '0x1c', '0x16']
ntfs = ['0x07', '0x17', 'Basic data partition']

'''
Gets the MD5 Hash of the Disk Image, shows information via MMLS, counts number of partitons found in disk image
Returns list of partition_information and partion count.
'''
def parse_mmls(img_path):
    # use mmls to get a list of partitions.
    md5sum_output = subprocess.getoutput("md5sum {0}".format(img_path))
    print("MD5 hash of DD image is: {0}".format(md5sum_output))
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
            print("")
    return partition_info, part_count

# Carves out specific partion from dd and gets specific information of each separate partition, tools used fsstat, fls
def get_file_sys_info(img_path,partition_info, part_count):

    # List that will contain names of partitions created
    all_partitions = {}

    # for loop to get all of the partitions and make separate partions
    for i in range(part_count):
        skip = partition_info[i]["Start"]
        count = partition_info[i]["Length"]
        subprocess.getoutput("dd if={0} skip={1} count={2} bs=512 of=partition_{3}.dd".format(img_path,skip,count,i))
        print("partition_{0}.dd has been created".format(i))
        all_partitions[i] = "partition_{0}.dd".format(i)
        print("\nFull Partition List - {0}".format(all_partitions))
        
    # for loop to get the MD5 Hash of each partion as well as fsstat and fls 
    for parts in all_partitions:
        print("\n################--PARTITION {0} FILE SYSTEM INFORMATIOM--################\n".format(parts))
        md5out = subprocess.getoutput("md5sum {0}".format(all_partitions[parts]))
        print("MD5 Hash: {0}\n".format(md5out))

        real_filetype = subprocess.getoutput("fsstat -t {0}".format(all_partitions[parts]))
        fsstat_info = subprocess.getoutput("fsstat {0} | head -36".format(all_partitions[parts]))
        print("FSSTAT OUTPUT {0}".format(fsstat_info))

        fls_rd_output = subprocess.getoutput("fls -f {0} -rd {1}".format(real_filetype,all_partitions[parts]))
        print("FLS OUTPUT - Recently Deleted Files \n")
        print(fls_rd_output)

    # Just for formatting for some separation
    print("\n------------------------------------------------------------------------------------\n")
   
    # returns list of all partitions 
    return all_partitions

# Uses tsk_recover to recover all files including allocated and unallocated and stores it in a local directory
def recover_by_tsk(partition_list):    

    print("Creating local recovery directory to recover deleted files for each partition\n")

    # make a recovery directory 
    subprocess.getoutput("mkdir recovery")

    for p in partition_list:
        subprocess.getoutput("mkdir recovery/part{0}".format(p))
        tsk_recover_outp = subprocess.getoutput("tsk_recover -e {0} ./recovery/part{1}".format(partition_list[p],p))
        print("Partition {0}'s Deleted Files recovered and stored in local directory at ./recovery/part{0}".format(p))
        print(tsk_recover_outp)
        print("")

    return

def main(argv):
    inputfile = ''

    if len(sys.argv) < 2:
        print("\nERROR: Please provide the path to the disk image\n")
        print("Usage: forensic_scripty.py -i <inputfile>\n")
        exit()
    try:
        opts, args = getopt.getopt(argv,"hi:",["ifile="])
    except getopt.GetoptError:
        print("\nERROR: Improper arguments passed. -h for help\n")
        print ('CORRECT USAGE: forensic_scripty.py -i <inputfile>\n')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('\nUSAGE: forensic_scripty.py -i <inputfile>\n')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg

    img_path = inputfile

    print("\nThis script may take some time please be patient :) \n")

    partition_info, part_count = parse_mmls(img_path)
    partition_list = get_file_sys_info(img_path,partition_info, part_count)
    recover_by_tsk(partition_list)




if __name__ == "__main__":
    main(sys.argv[1:])
    