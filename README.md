# saisoku
Saisoku is a Python (2.7, 3.6 tested) module that helps you build complex pipelines of batch file copying jobs. It uses threaded file copying for fast file transfers and supports txt file lists. Uses Luigi for task management and web ui. To learn more about Luigi, see it's [github](https://github.com/spotify/luigi) or [readthedocs](https://luigi.readthedocs.io/en/stable/index.html).

## Requirements
- luigi
- pyfastcopy
- tqdm
- scandir

Install above python modules using pip

```sh
$ pip install -r requirements.txt
```

## Usage
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

With the Luigi centralized scheduler running, we can send a copy files task to Luigi (see below for parameters)
```sh
$ python run_luigi.py CopyFiles --src /source/path --dst /dest/path --filelist=filelist.txt
```

### HTTP copy

Start up at least 4 http tornado servers (tserv)
```sh
$ python tserv.py /src/dir
$ python tserv.py /src/dir --port 8001
python tserv.py /src/dir --port 8002
python tserv.py /src/dir --port 8003
```
This will create an index.html file on http://localhost serving up the files in /src/dir.

To send a HTTP copy files task to Luigi
```sh
$ python run_luigi.py CopyFilesHTTP --src http://localhost --dst /dest/path
```

Log for saisoku is in os env temp folder saisoku.log.


### ThreadedCopy

Saisoku's `ThreadedCopy` class requires two parameters:

`src` source directory containing files you want to copy

`dst` destination directory of where you want the files to go (directory will be created if not there already)

Optional parameters:

`filelist` optional txt file containing one filename per line (not full path)

`ignore` optional ignore files tuple, example `('*.pyc', 'tmp*')`

`threads` number of worker copy threads (default 16)

`symlinks` copy symlinks (default False)

`copymeta` copy file stat info (default True)


```
>>> from saisoku import ThreadedCopy

>>> ThreadedCopy(src='/source/dir', dst='/dest/dir', filelist='filelist.txt', ignore=('tmp*'))
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

`threads` number of worker copy threads (default 16)

`tservports` tornado server (tserv) ports, these ports will be load balanced (default (8000,8001,8002,8003))

`fetchmode` file get mode, either requests or urlretrieve (default urlretrieve)

`chunksize` chunk size for requests fetchmode (default 16384)

```
>>> from saisoku import ThreadedHTTPCopy

>>> ThreadedHTTPCopy('http://localhost', '/dest/dir')
```
