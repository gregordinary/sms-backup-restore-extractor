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
#
# Links :
#   https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore
#
#  example: python smsbackuprestore-extractor.py sms-20141122183844.xml medias/
#
# 2019-02-09 @stefan-schiffer 
# Ported to Python 3
# You might have first to fix malformed XML with entityfixer.py
# https://gist.github.com/Calvin-L/5232f876b8acf48a216941b8904632bb
#
# 2023-09-08 @gregordinary
# Added multi-threading, duplicate handling, directory support, other improvements
#
# The script saves the hashes of the created files in a file named 'saved_hashes.pkl'
# in the output directory, to avoid duplicates across multiple runs.
# If you want to reset the saved hashes, delete 'saved_hashes.pkl'.


# Initial Standard Library Imports
import os
import sys

# Third-Party & Conditional Imports
try:
    from lxml import etree
except ModuleNotFoundError:
    print("The required 'lxml' module is not installed.")
    print("You can install it by running 'pip install lxml' in your command line.")
    sys.exit(1)

if sys.platform == 'win32':
    try:
        from win32_setctime import setctime 
    except ImportError:
        print("win32-setctime module not installed. To install, run: pip install win32-setctime")
        sys.exit(1)

# Remaining Standard Library Imports
import argparse
import base64
import datetime
import hashlib
import logging
import pickle
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Define the is_windows flag
is_windows = sys.platform == 'win32'

def process_mms(mms, output_folder, saved_hashes):
    media_list = get_media_list(mms)
    folder = get_folder_name(mms)
    folder_hashes = saved_hashes.get(folder, set())
    output = get_output_folder(output_folder, folder)

    for media in media_list:
        rawdata, sha256, filename = get_file_data(media)

        if sha256 in folder_hashes:
            logging.info("Duplicate file skipped: %s", filename)
            continue

        outfile = os.path.join(output, filename)
        timestamp = datetime.datetime.fromtimestamp(float(mms.get("date")) / 1000.0)

        write_file(outfile, rawdata, timestamp, is_windows)
        folder_hashes.add(sha256)

    update_saved_hashes(saved_hashes, folder, folder_hashes)
    mms.clear()

def get_media_list(mms):
    return mms.xpath(".//part[starts-with(@ct, 'image') or starts-with(@ct, 'video')]")

def get_folder_name(mms):
    address = mms.get("address")
    contact = mms.get("contact_name")
    if contact == "(Unknown)":
        folder = address if address is not None else "_Unknown"
    else:
        folder = contact
    return folder

def get_output_folder(output_folder, folder):
    output = os.path.join(output_folder, folder)
    if not os.path.exists(output):
        os.makedirs(output)
        logging.info("New folder created: %s", folder)
    return output

def get_file_data(media):
    rawdata = base64.b64decode(media.get("data"))
    sha256 = hashlib.sha256(rawdata).hexdigest()
    filename = media.get("cl")
    if filename == "null":
        name = media.get("ct")
        ext = name.split('/')[1]
        if ext == "jpeg":
            ext = "jpg"
        elif name == "image/*":
            logging.info("Unknown image type * for MMS content; guessing .jpg %s", output)
            ext = "jpg"
        elif name == "video/*":
            logging.info("Unknown video type * for MMS content; guessing .3gpp %s", output)
            ext = "3gpp"
        timestamp = datetime.datetime.fromtimestamp(float(mms.get("date")) / 1000.0)
        filename = timestamp.strftime("%Y%m%d_%H%M%S") + '.' + ext
    return rawdata, sha256, filename

def write_file(outfile, rawdata, timestamp, is_windows):
    try:
        with open(outfile, 'wb') as f:
            f.write(rawdata)
    except IOError as e:
        logging.error("Unable to write to file %s: %s", outfile, e)
        return

    if os.path.exists(outfile):
        filetime = (timestamp - datetime.datetime(1970, 1, 1)).total_seconds()
        try:
            if is_windows:
                setctime(outfile, filetime)
            else:
                filetime_ns = int(filetime * 1e9)
                os.utime(outfile, ns=(filetime_ns, filetime_ns, filetime_ns))
        except Exception as e:
            logging.error("Unable to set the file time for %s: %s", outfile, e)

def update_saved_hashes(saved_hashes, folder, folder_hashes):
    saved_hashes[folder] = folder_hashes


def main(input_path, output_folder, num_threads, saved_hashes_file, max_depth, huge_tree):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    output_folder = Path(output_folder)

    try:
        with open(saved_hashes_file, 'rb') as f:
            saved_hashes = pickle.load(f)
    except FileNotFoundError:
        saved_hashes = {}
    except IOError as e:
        logging.error("Unable to read saved hashes file: %s", e)
        return

    # Use ThreadPoolExecutor to process MMS in parallel
    futures = []
        
    # Check if input_path is a file or a directory
    if os.path.isfile(input_path):
        # Process single XML file
        input_file = input_path
        logging.info("Parsing: %s", input_file)
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for _, mms in etree.iterparse(input_file, tag='mms', huge_tree=huge_tree):
                futures.append(executor.submit(process_mms, mms, output_folder, saved_hashes))
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error("Exception: %s", e)
    else:
        # Process all XML files in input_path and its subdirectories
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for root, dirs, files in os.walk(input_path):
                depth = root[len(input_path):].count(os.path.sep)
                if max_depth is not None and depth > max_depth:
                    del dirs[:]
                for file in files:
                    if file.endswith(".xml"):
                        input_file = os.path.join(root, file)
                        logging.info("Parsing: %s", input_file)
                        for _, mms in etree.iterparse(input_file, tag='mms', huge_tree=huge_tree):
                            futures.append(executor.submit(process_mms, mms, output_folder, saved_hashes))
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error("Exception: %s", e)

    # Save the saved_hashes file
    try:
        with open(saved_hashes_file, 'wb') as f:
            pickle.dump(saved_hashes, f)
    except IOError as e:
        logging.error("Unable to write saved hashes file: %s", e)

    logging.info("Job done")
    logging.info("Output folder: %s", output_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SMSBackupRestore extractor')
    parser.add_argument('input_path', type=str,
                        help='Path to the input XML file or directory containing XML files')
    parser.add_argument('output_folder', type=str,
                        help='Path to the output folder')
    parser.add_argument('--threads', type=int, default=4,
                        help='Number of threads to use (default: 4)')
    parser.add_argument('--saved-hashes', type=str, default=None,
                        help='Path to the saved_hashes file (default: output_folder/saved_hashes.pkl)')
    parser.add_argument('--max-depth', type=int, default=None,
                        help='Maximum directory depth to search for XML files (default: no limit)')
    parser.add_argument('--huge-tree', action='store_true',
                        help='Disable lxml security features for very large XML files (not recommended)')

    args = parser.parse_args()

    if args.saved_hashes is None:
        saved_hashes_file = os.path.join(args.output_folder, 'saved_hashes.pkl')
    else:
        saved_hashes_file = args.saved_hashes

    main(args.input_path, args.output_folder, args.threads, saved_hashes_file, args.max_depth, args.huge_tree)
