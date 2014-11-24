#!/usr/bin/env python
# -*- coding: utf8 -*-

# SMSBackupRestore extractor
#
# smsbackuprestore-extractor.py
# 24/11/2014
#
# This script will extract all images and videos retrieved
# from a xml backup of the Android application "SMS Backup & Restore".
# For each contact, it will create a folder inside the output folder
# with all received images and videos.
# 
# Make sure the destination folder is empty otherwise it will create duplicates.
#
# Links :
#   https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore
#
#  example: python smsbackuprestore-extractor.py sms-20141122183844.xml medias/

from lxml import etree
import os
import sys

if len(sys.argv) < 2:
	print "usage: %s [sms-backup.xml] [output-folder]" % sys.argv[0]
	sys.exit(-1)

INPUT_FILE = sys.argv[1]	
OUTPUT_FOLDER = sys.argv[2]

if not os.path.isfile(INPUT_FILE):
	print "File %s not found" % INPUT_FILE

print "[*] Parsing : %s" % INPUT_FILE
tree = etree.parse(INPUT_FILE) 
mms_list = tree.xpath(".//mms")
total = 0
for mms in mms_list:
	address = mms.get("address")
	contact = mms.get("contact_name")
	if contact == "(Unknown)":
		folder = address
		if address == None:
			folder = "_Unknown"
	else:
		folder = contact
	media_list = mms.xpath(".//part[starts-with(@ct, 'image') or starts-with(@ct, 'video')]")
	# Create the folders
	for media in media_list:
		total = total + 1
		output = OUTPUT_FOLDER + "/" + folder
		if os.path.exists(output) == False:
			os.makedirs(OUTPUT_FOLDER + "/" + folder)
			print "[+] New folder created : %s" % output.encode("utf-8")
		filename = media.get("cl")
		rawdata = media.get("data").decode("base64")
		outfile = output + "/" + filename
		# Duplicates handling
		i = 1
		while os.path.isfile(outfile):
			dname = filename.split('.')
			dname.insert(-1, str(i))
			outfile = output + "/" + '.'.join(dname)
			i = i+1
		f = open(outfile, 'w')
		f.write(rawdata)
		f.close()
print "[*] Job done (%d files created)" % total
print "[*] Output folder : %s" % OUTPUT_FOLDER
