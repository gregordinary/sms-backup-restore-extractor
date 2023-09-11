# XML Entity Processing Script

This script processes XML entities in a file and fixes incorrect numeric XML entities. It is intended to repair malformed XML files for the backup utility "SMS Backup & Restore". 
The repaired files can then be run through the smsbackuprestore-extractor.py script in the parent directory, to extract media files from the XML and into directories.

## Usage

`xml-entity-fixer.py <input_file> <output_file>`

## Positional Arguments
- `input_file`: The path to the input file.
- `output_file`: The path to the output file.

## Optional Arguments
- `--chunk-size`: The size of the chunks to process the file in kilobytes. Default is 64KB.
- `--input-encoding`: The encoding of the input file. Default is 'utf-8'.
- `--output-encoding`: The encoding of the output file. Default is 'utf-8'.

## How It Works
The script reads the input file in chunks and processes each chunk to fix any incorrect numeric XML entities. It then writes the processed chunk to the output file.

1. It first looks for numeric XML entities, which are numbers enclosed in & and ;, e.g., `&#55357;&#56860;`.
2. For each entity, it converts the number to its corresponding Unicode character.
3. If the number is greater than or equal to 0x10000, it uses `chr` to convert the number to a Unicode character. Otherwise, it uses `struct.pack` to convert the number to a UTF-16 encoded byte string and then decodes the byte string to a Unicode string.
4. The script also handles incomplete XML entities and CDATA sections at the end of a chunk by moving them to the next chunk.

## Progress Bar
The script prints a progress bar to the console to indicate the progress of the processing. The progress bar shows the percentage of the file that has been processed.

## Summary
At the end of the processing, the script prints a summary of the processing, including:

- Runtime
- Number of changes made
- Chunk size
- Input file size
- Output file size

**Sample Summary Output:**
```
---- Summary ----
Runtime: 79.63 seconds
Changes Made: 526
Chunk Size: 64 KB
Input File Size: 2971.29 MB
Output File Size: 2971.18 MB
```
