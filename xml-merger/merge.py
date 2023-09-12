import argparse
import logging
import os
import sqlite3
import xml.etree.ElementTree as ET

# Initialize Logging
logging.basicConfig(level=logging.ERROR)

# Constants
SQL_CREATE_SMS_TABLE = '''CREATE TABLE IF NOT EXISTS sms_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT,
                        date TEXT,
                        xml_data TEXT UNIQUE)'''

SQL_CREATE_SEEN_TABLE = '''CREATE TABLE IF NOT EXISTS seen_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT,
                        date TEXT,
                        UNIQUE (address, date))'''

# Specify the batch size for batch insert
BATCH_SIZE = 1000  # Adjust this as needed

def setup_db(conn):
    """Initialize the SQLite database."""
    cursor = conn.cursor()
    cursor.execute(SQL_CREATE_SMS_TABLE)
    cursor.execute(SQL_CREATE_SEEN_TABLE)
    conn.commit()

def batch_insert(conn, data_batch):
    """Inserts records in batches."""
    cursor = conn.cursor()
    cursor.executemany('INSERT OR IGNORE INTO sms_data (address, date, xml_data) VALUES (?, ?, ?)', data_batch)
    cursor.executemany('INSERT OR IGNORE INTO seen_records (address, date) VALUES (?, ?)', [(x[0], x[1]) for x in data_batch])
    conn.commit()

def read_and_insert_xml(conn, file_name, use_iterparse=False):
    """Reads XML data and inserts it into the database."""
    data_batch = []
    cursor = conn.cursor()

    if use_iterparse:
        # Initialize variables to keep track of the currently processed elements and text
        current_elem = None
        current_address = None
        current_date = None

        for event, elem in ET.iterparse(file_name, events=("start", "end")):
            if event == "start":
                if elem.tag in ['sms', 'mms']:
                    current_elem = elem
                    current_address = elem.get('address')
                    current_date = elem.get('date')
            elif event == "end":
                if elem.tag in ['sms', 'mms']:
                    xml_data = ET.tostring(current_elem, encoding='unicode')
                    
                    cursor.execute('SELECT 1 FROM seen_records WHERE address=? AND date=?', (current_address, current_date))
                    if cursor.fetchone() is None:
                        data_batch.append((current_address, current_date, xml_data))

                    if len(data_batch) >= BATCH_SIZE:
                        batch_insert(conn, data_batch)
                        data_batch = []

                    # Clean up memory as elements are processed
                    elem.clear()

    else:
        try:
            tree = ET.parse(file_name)
        except ET.ParseError as e:
            logging.error(f"Failed to parse {file_name}: {e}")
            return

        root = tree.getroot()
        for tag_name in ['sms', 'mms']:
            for elem in root.findall(tag_name):
                address = elem.get('address')
                date = elem.get('date')
                xml_data = ET.tostring(elem, encoding='unicode')

                cursor.execute('SELECT 1 FROM seen_records WHERE address=? AND date=?', (address, date))
                if cursor.fetchone() is None:
                    data_batch.append((address, date, xml_data))

                if len(data_batch) >= BATCH_SIZE:
                    batch_insert(conn, data_batch)
                    data_batch = []

    if data_batch:
        batch_insert(conn, data_batch)

def write_to_output(conn, output_file):
    """Writes database records to an XML file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
            f.write('<smses>\n')
            
            cursor = conn.cursor()
            for row in cursor.execute('SELECT xml_data FROM sms_data'):
                xml_data = row[0]
                f.write(xml_data)
                f.write("\n")
            
            f.write('</smses>')
    except IOError as e:
        logging.error(f"File I/O error: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Process XML files and store into SQLite")
    parser.add_argument("-i", "--input", type=str, nargs='+', help="Input XML files or SQLite DB", required=True)
    parser.add_argument("-o", "--output", type=str, help="Output XML file", default=None)
    parser.add_argument("--db-file", type=str, help="SQLite DB file to store data", default=":memory:")
    parser.add_argument("--db-only-write", action="store_true", help="Only write to the SQLite DB, do not generate output XML")
    parser.add_argument("--input-db", action="store_true", help="Use SQLite DB as input for generating output XML")
    
    args = parser.parse_args()

    if args.db_only_write and args.output:
        raise ValueError("Can't specify both --db-only-write and -o")

    if args.input_db and args.db_only_write:
        raise ValueError("Can't specify both --input-db and --db-only-write")

    try:
        with sqlite3.connect(args.db_file) as conn:
            setup_db(conn)
            
            # Determine whether to use iterparse based on the database file location
            use_iterparse = bool(args.db_file and args.db_file != ":memory:")

            if args.input_db:
                if args.output:
                    write_to_output(conn, args.output)
            else:
                input_files = []
                for input_item in args.input:
                    if os.path.isdir(input_item):
                        for root, dirs, files in os.walk(input_item):
                            input_files.extend([os.path.join(root, file) for file in files if file.endswith('.xml')])
                    else:
                        input_files.append(input_item)

                # This loop now exists within the scope where input_files is defined.
                for input_file in input_files:
                    read_and_insert_xml(conn, input_file, use_iterparse=use_iterparse)

                if args.output and not args.db_only_write:
                    write_to_output(conn, args.output)
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()

