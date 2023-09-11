import argparse
import io
import os
import re
import struct
import sys
import time

# Regular expression for matching numeric XML entities, e.g. "&#55357;&#56860;".
rgx1 = re.compile(r"(?:&#\d+;)+")

# Regular expression to capture one of the numbers inside an entity.
rgx2 = re.compile(r"&#(\d+);")

# Per "struct" module docs, 'H' format character is used to read or write two-byte unsigned numbers.
UNSIGNED_SHORT = "H"

def print_progress_bar(completed, total, length=50):
    # Calculate progress as a percentage.
    progress = int(length * completed / total)
    bar = '[' + '#' * progress + '.' * (length - progress) + ']'
    percent = completed / total * 100
    # Print progress bar.
    sys.stdout.write("\rProgress: {} {:.2f}%".format(bar, percent))

def shorts_as_utf16(short_sequence):
    # Convert a sequence of shorts (numbers < 65536) into a UTF-16 string.
    try:
        format = 'H' * len(short_sequence)
        bits = struct.pack(format, *short_sequence)
        return bits.decode('utf-16')
    except struct.error as e:
        print("Error packing short_sequence:", short_sequence)
        raise e

def fix_codepoints(s, raw=False):
    # Fix numeric XML entities in a string.
    matches = list(rgx1.finditer(s))
    if not matches:
        return s
    with io.StringIO() as out:
        i = 0
        for m in matches:
            out.write(s[i:m.start()])
            i = m.end()
            nums = [int(i) for i in rgx2.findall(m.group(0))]
            if all(num < 0x10000 for num in nums):
                repl = shorts_as_utf16(nums)
            else:
                repl = ''.join(chr(num) for num in nums)
            if raw:
                out.write(repl)
            else:
                for c in repl:
                    out.write("&#{};".format(ord(c)))
        out.write(s[i:])
        return out.getvalue()

def process_file(input_file, output_file, chunk_size_kb=64, input_encoding='utf-8', output_encoding='utf-8'):
    # Process an XML file and fix numeric XML entities in the file.
    start_time = time.time()
    # Convert chunk_size_kb to bytes.
    chunk_size = chunk_size_kb * 1024
    total_size = os.path.getsize(input_file)
    processed_size = 0
    changes_made = 0
    try:
        # Open input and output files.
        with open(input_file, 'r', encoding=input_encoding) as inputFile, open(output_file, "w", encoding=output_encoding) as outputFile:
            leftover = ''
            while True:
                # Read a chunk of the input file.
                raw_chunk = leftover + inputFile.read(chunk_size)
                if not raw_chunk:
                    break
                
                # Update the processed size and print the progress bar.
                processed_size += len(raw_chunk.encode(input_encoding)) - len(leftover.encode(input_encoding))
                print_progress_bar(processed_size, total_size)
                
                # Check if the chunk ends with an incomplete XML entity or CDATA section.
                incomplete_entity = re.search(r'&#[0-9]*$|<!\[CDATA\[.*', raw_chunk)
                if incomplete_entity:
                    # Move the incomplete XML entity or CDATA section to the next chunk.
                    leftover = incomplete_entity.group()
                    raw_chunk = raw_chunk[:incomplete_entity.start()]
                else:
                    leftover = ''
                
                # Fix the numeric XML entities in the chunk.
                sanitized_chunk = fix_codepoints(raw_chunk, raw=True)
                if sanitized_chunk != raw_chunk:
                    changes_made += 1
                # Write the processed chunk to the output file.
                outputFile.write(sanitized_chunk)

        end_time = time.time()
        runtime = end_time - start_time
        
        # Print summary statistics.
        print("\n\n---- Summary ----")
        print("Runtime: {:.2f} seconds".format(runtime))
        print("Changes Made: {}".format(changes_made))
        print("Chunk Size: {} KB".format(chunk_size_kb))
        print("Input File Size: {:.2f} MB".format(total_size / (1024 * 1024)))
        print("Output File Size: {:.2f} MB".format(os.path.getsize(output_file) / (1024 * 1024)))
    except FileNotFoundError as e:
        print(f"\nFile not found: {e}")
    except PermissionError as e:
        print(f"\nPermission error: {e}")
    except Exception as e:
        print(f"\nError: {e}")


def main():
    # Define command line arguments.
    parser = argparse.ArgumentParser(description="Process and fix XML entities in a file.")
    parser.add_argument("input_file", help="Input file path")
    parser.add_argument("output_file", help="Output file path")
    parser.add_argument("--chunk-size", type=int, default=64, help="Chunk size in KB (default: 64KB)")
    parser.add_argument("--input-encoding", default='utf-8', help="Encoding of the input file")
    parser.add_argument("--output-encoding", default='utf-8', help="Encoding of the output file")

    # Parse command line arguments and process the file.
    args = parser.parse_args()
    process_file(args.input_file, args.output_file, args.chunk_size, args.input_encoding, args.output_encoding)

if __name__ == "__main__":
    main()
