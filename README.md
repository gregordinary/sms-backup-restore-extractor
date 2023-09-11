# sms-backup-restore-extractor
Forked from a [revision](https://gist.github.com/tetrillard/759bf2d165b440e4915c?permalink_comment_id=3057351#gistcomment-3057351) of [smsbackuprestore-extractor.py](https://gist.github.com/tetrillard/759bf2d165b440e4915c).

## SMSBackupRestore extractor
The purpose of this script is to extract all images and videos from an XML backup of the Android application "SMS Backup & Restore". For each contact, it creates a folder inside the output folder with all received images and videos. 

### Features
- Extracts images and videos from an SMS Backup & Restore XML file.
- Can point at an individual XML file or a directory of XML files. 
- Creates a separate folder for each contact in the specified output folder.
- Multithreading support for faster processing. Specify with --threads 
- Optional command Line Arguments
- Duplicate avoidance:
  - Saved Hashes File (saved_hashes.pkl)
    - Default location is in the specified output folder. 
    - Records SHA256 values for each media item processed for a given folder
    - If an image with a matching hash already exists in the target folder, it is skipped to avoid duplication.
    - Images may still be duplicated across separate folders (The same image was sent in different conversations).
    - Can specify a name or an existing file with --saved-hashes </path/to/saved_hash_file.pkl>
    - Saving separate hash files can be used to track multiple backups from unique devices.
  - Auto-alphabetize contacts when naming group MMS folders.
    - Contacts in group messages are arranged alphabetically for folder's name.
    - This ensures images from group conversations across multiple backups will end up in the same folder.
      - Example: Backup 1 has a conversation referenced as "Alice, Bob, Chris" and Backup 2 has a conversation referenced as "Bob, Alice, Chris", the folder name will be "Alice, Bob, Chris". The sort uses both Name and Address (phone number) values so ensure it is the same "Alice".  

### Usage
1. **Command Line Arguments**: The script takes several command line arguments:
    - Input:
      - `input_file(s) One or more .xml files to process. 
      - `input_path`: Path to a directory containing XML files in the root or in its sub-directories. 
    - `output_folder`: Path to the output folder.
    - `--huge-tree`: **(Likely Required)** When --huge-tree is specified, it disables an lxml security feature to support very large XML files.
    - `--threads`: (Optional) Number of threads to use (default: 1).
    - `--write-hash-on`: Specifies how frequently to update the saved_hashes.pkl file.
      - `--write-hash-on media` Default behavior. Will update the hash file after processing each media item (image or video). Creates the hash file immediately script execution and updates the hashes as it processes each media item. If the script is interrupted or terminated, the hash values of written items are tracked. 
      - `--write-hash-on mms` Update the hash file after processing each mms. Although unlikely due to the MMS size-limits, if your XML file has multiple images per MMS, this can offer slight performance improvement while still tracking progress. It will update the hash file as it processes each MMS object. 
      - `--write-hash-on xml` Update the hash file after processing an XML file.
        - Example: If you are processing a directory with 3 XML files and it errors out on the third file, your progress will be saved from the frist two files, but not the third. A trade-off for some additional performance, if needed. 
      - `--write-hash-on run` = Update the hash file only after processing the full run and exiting successfully. Whether there is 1 XML file or 10, it will only write the hash file at the end of a complete run. If the script exits unexpectedly, no hash file will be available to track duplicates between runs. This provides better performance at the risk of duplication.  
    - `--saved-hashes`: (Optional) Path to the saved_hashes file (default: output_folder/saved_hashes.pkl).
      - Useful for tracking backups of multiple devices. You could create and reference Alice_Android.pkl and Bob_Android.pkl when recovering each of their respective media files. Be sure to specify different output directories as well for each target user. 
    - `--max-depth`: (Optional) Maximum directory depth to search for XML files (default: current directory only). If you have multiple XML files located in multiple sub-directories, you can use this switch to have the script search through sub-directories up to a specified (or no) limit. The root of the target folder counts as the first folder, hence --max-depth 1. If you want the root plus one additional level deep, it would be --max-depth 2.
      - `--max-depth 0` = no limit
      - `--max-depth 1` = current directory only (default)
      - `--max-depth 2` = current directory + one additional level of subdirectories to search for XML files.
    - `--log-to-console`: By default, events are written to the log file xml-extract.log and can be viewed there. To view events as they are processed, add --log-to-console when running the script and it will display the output as it processes. This is useful for very large files if you want to make sure the process has not stalled.

2. **How to Run**: 
   - Install Python 3
   - Install the required Python modules by running `pip install lxml` and `pip install prettytable`. Additionaly, `pip install win32-setctime` if on Windows.
   -    - If you want to reset the saved hashes, delete or move 'saved_hashes.pkl' from the output directory.
   - Run the script with the required command line arguments. For example:
    ```
    python smsbackuprestore-extractor.py input_folder output_folder --threads 4 --saved-hashes alice_saved_hashes.pkl --max-depth 5 --huge-tree
    ```
    This command will process all XML files in `input_folder` and its subdirectories up to a depth of 5, using 4 threads, and save the extracted images and videos to the path specified in `output_folder`. The hashes of created files will be saved to `alice_saved_hashes.pkl`.

3. **Error Handling**: Basic error handling is implemented. By default files are written to xml-extract.log in the same directory as the script.
   - You can edit log_filename = "xml-extract.log" within the script if you wish the change the name or location of the log file.
   - Use --log-to-console to output logs to the console as well.
   - If the script exits unexpectedly, it will display the errors on the console by default. 

4. **Stats**: At the end of each run, the console will output stats to a table, detailing the run time, files/folders created, how many images were skipped, and any errors. Example below was from processing ~25GB data using --threads 8.  
```
+--------------------------+--------+
| Metric                   | Value  |
+--------------------------+--------+
| Run Time                 | 3m 48s |
| Folders Created          |   91   |
| Files Created            | 10478  |
| Duplicate Images Skipped |  3379  |
| Total Errors             |   1    |
+--------------------------+--------+
```



