## SMS Backup & Restore Information 

### Official App (Not Affiliated with this Repository)
- https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore

### Data Structure & Samples from SyncTech
- [Fields in XML Backup Files](https://www.synctech.com.au/sms-backup-restore/fields-in-xml-backup-files/)
- [XSD Schema for SMS](https://synctech.com.au/wp-content/uploads/2018/01/sms.xsd_.txt)
- [Sample XML](https://synctech.com.au/wp-content/uploads/2018/01/sms-sample.xml_.txt)

### Blogs
- [Removing Duplicates from SMS Backup Restore](http://blog.radj.me/removing-duplicates-sms-backup-restore-xml-android)
- [Deduplicating SMS/MMS on Android](https://www.embrangler.com/2023/03/deduplicating-smsmms-on-android/)
  
### Other Repositories
- [SMS Backup & Restore Cleaner](https://github.com/pcraciunoiu/AndroidSMSBackupRestoreCleaner)
- [SMS Backup & Restore Extractor](https://gist.github.com/tetrillard/759bf2d165b440e4915c)
- [SMS Backup & Restore Parser](https://github.com/danzek/sms-backup-and-restore-parser)
- [XML Entity Fixer](https://gist.github.com/Calvin-L/5232f876b8acf48a216941b8904632bb)

### Notes
This repository contains tools to:
1. **[Repair](https://github.com/gregordinary/sms-backup-restore-scripts/tree/master/xml-fixer)** XML Files created by SMS Backup & Restore. Forked from XML Entity Fixer, linked above. 
2. **[Merge and deduplicate](https://github.com/gregordinary/sms-backup-restore-scripts/tree/master/xml-merger)** XML Files created by SMS Backup & Restore. Inspired by SMS Backup & Restore Cleaner, linked above.
3. **[Extract Images](https://github.com/gregordinary/sms-backup-restore-scripts/tree/master)** from XML Files created by SMS Backup & Restore. Forked from SMS Backup & Restore Extractor, linked above.

The backup files I have are between 13 and 16 GB in size. Many existing tools read the XML into memory before processing so they did not work for my files, hence the new tools above. 
