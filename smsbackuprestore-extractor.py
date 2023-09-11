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

try:
    from prettytable import PrettyTable
except ModuleNotFoundError:
    print("The required 'prettytable' module is not installed.")
    print("You can install it by running 'pip install prettytable' in your command line.")
    sys.exit(1)

# Remaining Standard Library Imports
import argparse
import base64
import datetime
import errno 
import hashlib
import logging
import pickle
import time
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Logging Configuration
log_filename = "xml-extract.log"

# Define the is_windows flag
is_windows = sys.platform == 'win32'

# Define the GlobalStats class
class GlobalStats:
    def __init__(self):
        self.lock = threading.Lock()
        self.total_folders_created = 0
        self.total_files_created = 0
        self.total_duplicate_images_skipped = 0
        self.total_errors = 0

    def increment_folders_created(self):
        with self.lock:
            self.total_folders_created += 1

    def increment_files_created(self):
        with self.lock:
            self.total_files_created += 1

    def increment_duplicate_images_skipped(self):
        with self.lock:
            self.total_duplicate_images_skipped += 1

    def increment_errors(self):
        with self.lock:
            self.total_errors += 1

def initialize_logging(log_to_console):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # create a file handler
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.INFO)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Create a console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    if log_to_console:
        # create a stream handler (console)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.INFO)
        consoleHandler.setFormatter(formatter)
        # add the handler to the logger
        logger.addHandler(consoleHandler)


def process_mms(mms, output_folder, saved_hashes, saved_hashes_file, write_hash_on, global_stats, lock):
    media_list = get_media_list(mms)
    folder = get_folder_name(mms)
    with lock:
        folder_hashes = saved_hashes.get(folder, set())
    output = get_output_folder(output_folder, folder, global_stats)

    for media in media_list:
        rawdata, sha256, filename = get_file_data(media)

        if sha256 in folder_hashes:
            logging.info("Duplicate file skipped: %s", filename)
            global_stats.increment_duplicate_images_skipped()
            continue

        outfile = os.path.join(output, filename)
        timestamp = datetime.datetime.fromtimestamp(float(mms.get("date")) / 1000.0)

        write_file(outfile, rawdata, timestamp, is_windows, global_stats)
        with lock:
           folder_hashes.add(sha256)
        
        if write_hash_on == 'media':
            with lock:
                update_saved_hashes(saved_hashes, folder, folder_hashes, saved_hashes_file, global_stats)
    
    if write_hash_on == 'mms':
        with lock:
            update_saved_hashes(saved_hashes, folder, folder_hashes, saved_hashes_file, global_stats)
        
    mms.clear()


def get_media_list(mms):
    return mms.xpath(".//part[starts-with(@ct, 'image') or starts-with(@ct, 'video')]")

def get_folder_name(mms):
    address = mms.get("address")
    contact = mms.get("contact_name")
    if contact == "(Unknown)":
        folder = address if address is not None else "Unknown"
    else:
        folder = contact
    return folder

def get_output_folder(output_folder, folder, global_stats):
    output = os.path.join(output_folder, folder)
    if not os.path.exists(output):
        os.makedirs(output)
        logging.info("New folder created: %s", folder)
        global_stats.increment_folders_created()
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
        date = media.get("date")
        if date is None:
            # handle the case where date is None, e.g., set a default date or skip this item
            timestamp = datetime.datetime.now()
        else:
            timestamp = datetime.datetime.fromtimestamp(float(date) / 1000.0)

        filename = timestamp.strftime("%Y%m%d_%H%M%S%f") + '_' + sha256[:5] + '.' + ext
    return rawdata, sha256, filename


def write_file(outfile, rawdata, timestamp, is_windows, global_stats):
    try:
        with open(outfile, 'wb') as f:
            f.write(rawdata)
        global_stats.increment_files_created()
        logging.info("File created: %s", outfile)
    except IOError as e:
        if e.errno == errno.ENOSPC:  # if the error is "No space left on device"
            logging.error("No space left on the output device.")
        elif e.errno == errno.EACCES:  # if the error is "Permission denied"
            logging.error("You don't have permission to create this file.")
        else:
            logging.error("Unknown error occurred while writing the file: %s", str(e))
        global_stats.increment_errors()
        return

    if os.path.exists(outfile):
        filetime = (timestamp - datetime.datetime(1970, 1, 1)).total_seconds()
        try:
            if is_windows:
                setctime(outfile, filetime)
            else:
                filetime_ns = int(filetime * 1e9)
                os.utime(outfile, ns=(int(filetime_ns), int(filetime_ns)))
        except Exception as e:
            logging.error("Unable to set the file time for %s: %s", outfile, e)
            global_stats.increment_errors()

def update_saved_hashes(saved_hashes, folder, folder_hashes, saved_hashes_file, global_stats):
    saved_hashes[folder] = folder_hashes
    try:
        with open(saved_hashes_file, 'wb') as f:
            pickle.dump(saved_hashes, f)
    except IOError as e:
        logging.error("Unable to write saved hashes file: %s", e)
        global_stats.increment_errors()

def load_saved_hashes(saved_hashes_file, global_stats):
    try:
        with open(saved_hashes_file, 'rb') as f:
            saved_hashes = pickle.load(f)
    except FileNotFoundError:
        saved_hashes = {}
    except IOError as e:
        logging.error("Unable to read saved hashes file: %s", e)
        global_stats.increment_errors()
        sys.exit(1)
    return saved_hashes

def process_xml_files(input_path, output_folder, num_threads, saved_hashes, saved_hashes_file, max_depth, huge_tree, write_hash_on, global_stats):
    lock = threading.Lock()
    futures = []
    xml_files_found = False
    
    def process_xml_file(input_file):
        nonlocal xml_files_found
        xml_files_found = True
        logging.info("Parsing: %s", input_file)
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for _, mms in etree.iterparse(input_file, tag='mms', huge_tree=huge_tree):
                futures.append(executor.submit(process_mms, mms, output_folder, saved_hashes, saved_hashes_file, write_hash_on, global_stats, lock))
            for future in as_completed(futures):
                try:
                    future.result()
                except lxml.etree.XMLSyntaxError as e:
                    logging.error("XML syntax error occurred while parsing the file: %s", str(e))
                    global_stats.increment_errors()
        if write_hash_on == 'xml':
            update_saved_hashes(saved_hashes, None, None, saved_hashes_file)

    # Check if input_path is a file or a directory
    if os.path.isfile(input_path):
        # Process single XML file
        process_xml_file(input_path)
    else:
        # Process all XML files in input_path and its subdirectories
        logging.debug("Starting os.walk on input_path: %s", input_path)
        for root, dirs, files in os.walk(input_path):
            depth = root[len(input_path):].count(os.path.sep)
            if max_depth == 0:
                for file in files:
                    if file.endswith(".xml"):
                        process_xml_file(os.path.join(root, file))
            elif depth > (max_depth - 2):
                del dirs[:]
            else:
                for file in files:
                    if file.endswith(".xml"):
                        process_xml_file(os.path.join(root, file))

    
    if not xml_files_found:
        logging.error("No XML files found in the specified input path.")
        global_stats.increment_errors()
        sys.exit(1)

def format_timedelta(td):
    days, seconds = td.days, td.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    milliseconds = td.microseconds // 1000

    if days:
        return f'{days}d {hours}h {minutes}m {seconds}s'
    elif hours:
        return f'{hours}h {minutes}m {seconds}s'
    elif minutes:
        return f'{minutes}m {seconds}s'
    elif seconds:
        return f'{seconds}s {milliseconds}ms'
    else:
        return f'{milliseconds}ms'

def main(input_paths, output_folder, num_threads, saved_hashes_file, max_depth, huge_tree, write_hash_on, log_to_console):
    global_stats = GlobalStats()
    initialize_logging(log_to_console)
    try:
        saved_hashes = load_saved_hashes(saved_hashes_file, global_stats)
    except IOError as e:
        logging.error("Unable to read saved hashes file: %s", e)
        global_stats.increment_errors()
        sys.exit(1)

    for input_path in input_paths:
        try:
            process_xml_files(input_path, output_folder, num_threads, saved_hashes, saved_hashes_file, max_depth, huge_tree, write_hash_on, global_stats)
        except Exception as e:
            logging.error("Exception: %s", e)
            global_stats.increment_errors()

    # display summary
    table = PrettyTable()
    table.field_names = ["Metric", "Value"]
    table.align["Metric"] = "l"
    table.align["Value"] = "c"
    table.add_row(["Run Time", format_timedelta(datetime.timedelta(seconds=(time.time() - start_time)))])
    table.add_row(["Folders Created", global_stats.total_folders_created])
    table.add_row(["Files Created", global_stats.total_files_created])
    table.add_row(["Duplicate Images Skipped", global_stats.total_duplicate_images_skipped])
    table.add_row(["Total Errors", global_stats.total_errors])
    print(table)

if __name__ == "__main__":
    start_time = time.time()

    parser = argparse.ArgumentParser(description='SMSBackupRestore extractor')
    parser.add_argument('input_path', type=str, nargs='+',
                        help='Path(s) to the input XML file(s) or directory containing XML files')
    parser.add_argument('output_folder', type=str,
                        help='Path to the output folder')
    parser.add_argument('--threads', type=int, default=4,
                        help='Number of threads to use (default: 4)')
    parser.add_argument('--saved-hashes', type=str, default=None,
                        help='Path to the saved_hashes file (default: output_folder/saved_hashes.pkl)')
    parser.add_argument('--max-depth', type=int, default=1,
                        help='Maximum directory depth to search for XML files (default: 1)')
    parser.add_argument('--huge-tree', action='store_true',
                        help='Disable lxml security features for very large XML files (not recommended)')
    parser.add_argument('--write-hash-on', type=str, default='media',
                        choices=['media', 'mms', 'xml', 'run'],
                        help='When to update the saved_hashes file (default: media)')
    parser.add_argument('--log-to-console', action='store_true',
                    help='Log to console in addition to the log file')

    args = parser.parse_args()

    if args.saved_hashes is None:
        saved_hashes_file = os.path.join(args.output_folder, 'saved_hashes.pkl')
    else:
        saved_hashes_file = args.saved_hashes

    main(args.input_path, args.output_folder, args.threads, saved_hashes_file, args.max_depth, args.huge_tree, args.write_hash_on, args.log_to_console)
