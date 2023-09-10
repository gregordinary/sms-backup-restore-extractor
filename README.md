# sms-backup-restore-extractor
Forked from a [revision](https://gist.github.com/tetrillard/759bf2d165b440e4915c?permalink_comment_id=3057351#gistcomment-3057351) of [smsbackuprestore-extractor.py](https://gist.github.com/tetrillard/759bf2d165b440e4915c).

## SMSBackupRestore extractor
The purpose of this script is to extract all images and videos from an XML backup of the Android application "SMS Backup & Restore". For each contact, it creates a folder inside the output folder with all received images and videos.

### Features
- Extracts images and videos from an XML backup.
- Creates a separate folder for each contact in the output folder.
- Avoids duplicates across multiple runs by saving the hashes of created files in a 'saved_hashes.pkl' file.
- Multi-thread support for parallel processing.
- Optional command Line Arguments 
- Saved Hash File:
  - Avoids duplicate images within the same folder across multiple runs.
  - Separate hash files can be kept to track imports for separate devices. 


### Improvements:
- Auto-alphabetize contacts when naming group MMS folders.
  - I.e., if you had one backup with a group MMS from Alice, Bob, and Chris, it would create a folder called "Alice Bob Chris". If in another backup you have the same participants ordered "Bob, Alice, and Chris", this script will sort the participants alphabetically so it still creates the folder "Alice Bob Chris" and you don't end up with separate folders for the same conversation. Contact name and address (phone number) are taken into account when sorting to ensure uniqueness. 


### Usage
1. **Command Line Arguments**: The script takes several command line arguments:
    - `input_path`: Path to the input XML file or directory containing XML files.
    - `output_folder`: Path to the output folder.
    - `--huge-tree`: (Likely Needed) Disable lxml security features to support very large XML files.
    - `--threads`: (Optional) Number of threads to use (default: 4).
    - `--write-hash-on`:
      - `--write-hash-on media` = Update the hash file after processing each media item. Default behavior, will create the hash file immediately on running the script and update the hashes as it processes each media item (image or video). If the script is interrupted or terminated, the hash values of written images is still tracked. 
      - `--write-hash-on mms` = Update the hash file after processing each mms. Although unlikely due to the MMS size-limits, if your XML file has multiple images per MMS, this can offer slight performance improvement while still tracking progress. It will update the hash file as it processes each MMS object. 
      - `--write-hash-on xml` = Update the hash after processing a complete XML file. If you are processing a directory with 3 XML files and it errors out on the third file, your progress will be saved from the frist two files, but not the third. A trade-off for some additional performance, if needed. 
      - `--write-hash-on run` = Update the hash file after processing the full run and exiting successfully. Whether there is 1 XML file or 10, it'll only produce the hash file at the end of a complete run (old behavior). If the script exits unexpectedly, while all your images will still be there in the directory, the tracking of them between runs will be lost. 
    - `--saved-hashes`: (Optional) Path to the saved_hashes file (default: output_folder/saved_hashes.pkl).
    - `--max-depth`: (Optional) Maximum directory depth to search for XML files (default: current directory only).
      - --max-depth 0 = no limit
      - --max-depth 1 = current directory only (default)
      - --max-depth 2 = current directory + one additional level of subdirectories to search for XML files.
      - etc. 

2. **How to Run**: 
   - If you want to reset the saved hashes, delete or move 'saved_hashes.pkl' from the output directory.
   - Install the required modules by running `pip install lxml` and additional `pip install win32-setctime` if on Windows.
   - Run the script with the required command line arguments. For example:
    ```
    python script.py input_folder output_folder --threads 4 --saved-hashes saved_hashes.pkl --max-depth 5 --huge-tree
    ```
    This command will process all XML files in `input_folder` and its subdirectories up to a depth of 5, using 4 threads, and save the extracted images and videos to `output_folder`. The hashes of created files will be saved to `saved_hashes.pkl`.

4. **Error Handling**: The script contains error handling for common issues such as being unable to read the `saved_hashes` file or write to the output folder. These errors will be logged and the script will stop execution. Additionally, any exception that occurs during the processing of an MMS will be caught and logged, but the script will continue processing the remaining MMS.



