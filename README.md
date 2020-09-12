# saisoku - Fast file transfer orchestration pipeline

<img align="left" width="226" height="200" src="docs/saisoku.png?raw=true" hspace="5" vspace="5" alt="saisoku">

Saisoku is a Python (2.7, 3.6 tested) package that helps you build complex pipelines of batch file/directory transfer/sync jobs. It supports threaded transferring of files locally, over network mounts, or HTTP. With Saisoku you can also transfer files to and from AWS S3 buckets and sync directories using Rclone and keep directories in sync "real-time" with Watchdog.

Saisoku includes a Transfer Server and Client which support copying over TCP sockets.

Saisoku uses Luigi for task management and web ui. To learn more about Luigi, see it's [github](https://github.com/spotify/luigi) or [readthedocs](https://luigi.readthedocs.io/en/stable/index.html).


[![License](https://img.shields.io/github/license/shirosaidev/saisoku.svg?label=License&maxAge=86400)](./LICENSE)
[![Release](https://img.shields.io/github/release/shirosaidev/saisoku.svg?label=Release&maxAge=60)](https://github.com/shirosaidev/saisoku/releases/latest)
[![Sponsor Patreon](https://img.shields.io/badge/Sponsor%20%24-Patreon-brightgreen.svg)](https://www.patreon.com/shirosaidev)
[![Donate PayPal](https://img.shields.io/badge/Donate%20%24-PayPal-brightgreen.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CLF223XAS4W72)


## Requirements
- luigi
- tornado
- scandir
- pyfastcopy
- tqdm
- requests
- beautifulsoup4
- boto3

Install above python modules using pip

```sh
$ pip install -r requirements.txt
```

## Download

```shell
$ git clone https://github.com/shirosaidev/saisoku.git
$ cd saisoku
```
[Download latest version](https://github.com/shirosaidev/saisoku/releases/latest)


## How to use

## Start Luigi

Create directory for state file for Luigi
```sh
$ mkdir /usr/local/var/luigi-server
```
Start Luigi scheduler daemon in foreground with
```sh
$ luigid --state-path=/usr/local/var/luigi-server/state.pickle
```
or in the background with
```sh
$ luigid --background --state-path=/usr/local/var/luigi-server/state.pickle --logdir=/usr/local/var/log
```
It will default to port 8082, so you can point your browser to http://localhost:8082 to access the web ui.

## Configure Boto 3

If you are going to use the S3 copy Luigi tasks, first start be setting up Boto 3 (aws sdk python module) with the quick start instructions at [boto 3 github](https://github.com/boto/boto3).

## Usage - Luigi tasks

### Local/network mount copy

With the Luigi centralized scheduler running, we can send a copy files task to Luigi 
```sh
$ python run_luigi.py CopyFiles --src /source/path --dst /dest/path
```

See below for the different [parameters](#using-saisoku-module-in-python) for each Luigi task.

### Tarball package copy
To run a copy package task, which will create a tar.gz (gzipped tarball) file containing all files at src and copy the tar.gz to dst
```sh
$ python run_luigi.py CopyFilesPackage --src /source/path --dst /dest/path
```

### HTTP copy

Start up 2 Saisoku http servers, the get requests from saisoku clients will be load balanced across these.
```sh
$ python saisoku_server.py --httpserver -p 5005 -d /src/dir
$ python saisoku_server.py --httpserver -p 5006 -d /src/dir
```
This will create an index.html file on http://localhost:5005 serving up the files in /src/dir.

To send a HTTP copy files task to Luigi
```sh
$ python run_luigi.py CopyFilesHTTP --src http://localhost --dst /dest/path --ports [5005,5006] --threads 2
```

### S3 copy

To copy a local file to s3 bucket
```sh
$ python run_luigi.py CopyLocalFileToS3 --src /source/file --dst s3://bucket/foo/bar
```

s3 bucket object to local file
```sh
$ python run_luigi.py CopyS3lFileToLocal --src s3://bucket/foo/bar --dst /dest/file
```

### Rclone sync

Saisoku can use Rclone to sync directories, etc. First, make sure you have [Rclone](https://rclone.org/) installed and in your PATH.

To to do a dry-run sync from source to dest using Rclone:
```sh
$ python run_luigi.py SyncDirsRclone --src /source/path --dst /dest/path
```

To sync from source to dest using Rclone
```sh
$ python run_luigi.py SyncDirsRclone --src /source/path --dst /dest/path --cmdargs '["-vv"]'
```

To change the subcommand that Rclone uses (default is sync)
```sh
$ python run_luigi.py SyncDirsRclone --src /source/path --dst /dest/path --command 'subcommand'
```

### Watchdog directory sync

Saisoku can use watchdog to keep directories synced in "real-time". First, make sure you have rsync installed and in your PATH.

To keep directories in sync from source to dest using Watchdog
```sh
$ python run_luigi.py SyncDirsWatchdog --src /source/path --dst /dest/path
```

## Usage - Server -> Client transfer

Start up Saisoku Transfer server listening on all interfaces on port 5005 (default)
```sh
$ python saisoku_server.py --host 0.0.0.0 -p 5005
```
Run client to download file from server
```sh
$ python saisoku_client.py --host 192.168.2.3 -p 5005 /path/to/file
```


## Log file

Saisoku output get logged to os env TEMP/TMPDIR directory in `saisoku.log` file.


## Using saisoku module in Python

### ThreadedCopy

Saisoku's `ThreadedCopy` class requires two parameters:

`src` source directory containing files you want to copy

`dst` destination directory of where you want the files to go (directory will be created if not there already)

Optional parameters:

`filelist` optional txt file containing one filename per line of files in src directory (not full path)

`ignore` optional ignore files list, example `['*.pyc', 'tmp*']`

`threads` number of worker copy threads (default 16)

`symlinks` copy symlinks (default False)

`copymeta` copy file stat info (default True)


```
>>> from saisoku import ThreadedCopy

>>> ThreadedCopy(src='/source/dir', dst='/dest/dir', filelist='filelist.txt')
calculating total file size..
100%|██████████████████████████████████████████████████████████| 173/173 [00:00<00:00, 54146.30files/s]
copying 173 files..
100%|██████████████████████████████████████████████| 552M/552M [00:06<00:00, 97.6MB/s, file=dk-9.4.zip]
```

### ThreadedHTTPCopy

Saisoku's `ThreadedHTTPCopy` class requires two parameters:

`src` source http tornado server (tserv) serving a directory of files you want to copy

`dst` destination directory of where you want the files to go (directory will be created if not there already)

Optional parameters:

`threads` number of worker copy threads (default 1)

`ports` tornado server (tserv) ports, these ports will be load balanced (default [5000])

`fetchmode` file get mode, either requests or urlretrieve (default urlretrieve)

`chunksize` chunk size for requests fetchmode (default 8192)

```
>>> from saisoku import ThreadedHTTPCopy

>>> ThreadedHTTPCopy('http://localhost', '/dest/dir')
```

### Rclone

Saisoku's `Rclone` class requires two parameters:

`src` source directory of files you want to sync

`dst` destination directory of where you want the files to go

Optional parameters:

 def __init__(self, src, dst, flags=[], command='sync', cmdargs=[]):

`flags` a list of Rclone flags (default [])

`command` subcommand you want Rclone to use (default sync)

`cmdargs` a list of command args to use (default ['--dry-run', '-vv'])

```
>>> from saisoku import Rclone

>>> Rclone('/src/dir', '/dest/dir')
```

### Watchdog

Saisoku's `Watchdog` class requires two parameters:

`src` source directory of files you want to sync

`dst` destination directory of where you want the files to go

Optional parameters:

 def __init__(self, src, dst, recursive, patterns, ignore_patterns, ignore_directories, case_sensitive)

`recursive` bool used for recurisvely checking all sub directories for changes (default True)

`patterns` file name patterns to use when checking for changes (default *)

`ignore_patterns` file name patterns to ingore when checking for changes (default *)

`ignore_directories` bool used for ignoring directories (default False)

`case_sensitive` bool used for being case sensitive (default True)


```
>>> from saisoku import Watchdog

>>> Watchdog('/src/dir', '/dest/dir')
```

## Patreon
If you are a fan of the project or using Saisoku in production, please consider becoming a [Patron](https://www.patreon.com/shirosaidev) to help advance the project.
