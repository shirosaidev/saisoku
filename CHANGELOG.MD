# saisoku Change Log

## [0.1-b.3] = 2019-02-22
### added
- copy package task (CopyFilesPackage class) for creating tar.gz of files in src directory and copying it to dst
- saisoku transfer server and client
- luigi tasks for copying files to and from aws s3 buckets
- requirement for boto3 (aws sdk python module)
- rclone Luigi task, requires rclone installed and in PATH
- Rclone class to saisoku module
### changed
- improved tserv.py
### fixed
- encoding issue with non-ascii characters and http file copy

## [0.1-b.2] = 2019-02-20
### added
- http file copying
- ThreadedHTTPCopy class
- additional requirements in requirements.txt for http file copying (tornado, requests, beautifulsoup4)

## [0.1-b.1] = 2019-02-19
### note
- first release
