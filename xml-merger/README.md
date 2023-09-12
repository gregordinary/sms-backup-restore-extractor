# XML Merger
# WORK IN PROGRESS

## Description

This script processes multiple XML files to combine the SMS and MMS messages they contain, avoiding duplicates. The data is temporarily stored in an SQLite database for efficient duplicate checking and data manipulation. The script allows various options for performance tuning and storage.

## Features

- Combine & deduplicate XML backup files created by the application SMS Backup & Restore.
- Option to store SQLite database in memory (default) or disk (required for handling large files)
- Deduplication handled by treating 'address'(phone number)+'date'(timestamp down to ms) as a combined key.
- Provides an option to toggle SQLite's synchronous mode for better performance or data integrity.
- Accepts input of single and multiple XML files, as well as directories containing XML files.

## Requirements

- Python 3.x

## Usage

### Basic Usage

Run `python3 merge.py -i <input1.xml> <input2.xml> -o <output.xml>`. This command combines and deduplicates the messages from `<input1.xml>` and `<input2.xml>` into `<output.xml>`, using an in-memory SQLite database.

### Store SQLite Database on Disk

Run `python3 merge.py -i <input1.xml> <input2.xml> -o <output.xml> --db-file mydatabase.db`. This command combines and deduplicates the messages from `<input1.xml>` and `<input2.xml>` into `<output.xml>`, and stores the SQLite database in `mydatabase.db`.

### Processing a Directory

Run `python3 merge.py -i ./my_xml_directory/ -o <output.xml>`. This command processes all `.xml` files within the directory `my_xml_directory` into `<output.xml>`.

### Ingest Files into DB

Run `python3 merge.py --db-only-write --db-file my_sms.db -i <input1.xml> <input2.xml>`. This command writes `<input1.xml>` and `<input2.xml>` to "my_sms.db".

### Use SQLite database as Input

Run `python3 merge.py --input-db --db-file my_sms.db -o <output.xml>`. Takes data from "my_sms.db" and creates a merged, deduplicated XML file from its data. 

### Toggling SQLite Synchronous Mode

Run `python3 merge.py -i <input1.xml> <input2.xml> -o <output.xml> --sync-mode OFF`. This command processes `<input1.xml>` and `<input2.xml>` with SQLite's synchronous mode set to `OFF` for better performance. 
**Note:** when running in asynchronous mode, if the process is interrupted, data may be lost.

## Command-Line Options

- `-i` or `--input`: The input XML file(s) or directory. (Required)
- `-o` or `--output`: The output XML file. (Requried)
- `--db-file`: SQLite DB file to store data. Defaults to in-memory if not specified. Specify this option when working with large files that won't fit in memory.
- `--db-only-write`: Write entries to the SQLite database without generating an output XML file. This is useful for accumulating data over multiple runs, before creating the combined XML.
- `--input-db`: Create a combined, deduplicated XML file directly from a SQLite database. 
- `--sync-mode`: SQLite Synchronous Mode. Options are `OFF`, `NORMAL`, and `FULL`. Default is `FULL`. 
