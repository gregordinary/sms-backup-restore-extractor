import sqlite3
import xml.etree.ElementTree as ET
import argparse
import os

BATCH_SIZE = 1000  # Adjust as needed

def setup_tables(conn):
    """Sets up tables in the database."""
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sms_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT,
                    date TEXT,
                    xml_data TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS seen_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT,
                    date TEXT,
                    UNIQUE (address, date))''')
    conn.commit()

def configure_sqlite(conn, sync_mode):
    """Configure SQLite settings for better performance."""
    conn.execute(f'PRAGMA synchronous = {sync_mode}')
    conn.execute('PRAGMA journal_mode = MEMORY')

def batch_insert(conn, data_batch):
    """Inserts a batch of records into the tables."""
    c = conn.cursor()
    c.executemany('INSERT OR IGNORE INTO sms_data (address, date, xml_data) VALUES (?, ?, ?)', data_batch)
    c.executemany('INSERT OR IGNORE INTO seen_records (address, date) VALUES (?, ?)', [(x[0], x[1]) for x in data_batch])
    conn.commit()

def process_xml(conn, file_name, output_root):
    """Reads an XML file and inserts records into the database and an output XML root."""
    tree = ET.parse(file_name)
    root = tree.getroot()
    data_batch = []

    c = conn.cursor()

    for tag_name in ['sms', 'mms']:
        for record in root.findall(tag_name):
            address = record.get('address')
            date = record.get('date')
            xml_data = ET.tostring(record, encoding='unicode')

            c.execute('SELECT 1 FROM seen_records WHERE address=? AND date=?', (address, date))
            if c.fetchone() is None:
                data_batch.append((address, date, xml_data))
                if output_root is not None:
                    output_root.append(record)

                if len(data_batch) >= BATCH_SIZE:
                    batch_insert(conn, data_batch)
                    data_batch = []

    if data_batch:
        batch_insert(conn, data_batch)

def main(db_file=':memory:', input_files=[], output_file=None):
    conn = sqlite3.connect(db_file)
    configure_sqlite(conn, args.sync_mode)
    setup_tables(conn)

    output_root = ET.Element("root") if output_file else None

    for input_file in input_files:
        process_xml(conn, input_file, output_root)

    if output_file:
        output_tree = ET.ElementTree(output_root)
        output_tree.write(output_file)

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process XML files and store into SQLite")
    parser.add_argument("-i", "--input", type=str, nargs='+', help="Input XML files or directory", required=True)
    parser.add_argument("-o", "--output", type=str, help="Output XML file", required=False)
    parser.add_argument("--db-file", type=str, help="SQLite DB file to store data", default=":memory:")
    parser.add_argument("--sync-mode", type=str, choices=['OFF', 'NORMAL', 'FULL'], default='FULL', help="SQLite Synchronous Mode")
    args = parser.parse_args()

    input_files = []
    for input_item in args.input:
        if os.path.isdir(input_item):
            for root, dirs, files in os.walk(input_item):
                input_files.extend([os.path.join(root, file) for file in files if file.endswith('.xml')])
        else:
            input_files.append(input_item)

    main(db_file=args.db_file, input_files=input_files, output_file=args.output)
