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
Create state file for Luigi
```sh
$ mkdir /usr/local/var/luigi-server && touch /usr/local/var/luigi-server/state.pickle
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

With the global Luigi scheduler running, we can send a copy files task to Luigi (see below for parameters)
```sh
$ python run_luigi.py CopyFiles --src /source/path --dst /dest/path --filelist=filelist.txt
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

`symlinks` copy symlinks (default false)

`copymeta` copy file stat info (default True)


```
>>> from saisoku import ThreadedCopy

>>> ThreadedCopy(src='/source/dir', dst='/dest/dir', filelist='filelist.txt', ignore=('tmp*'))
calculating total file size..
100%|██████████████████████████████████████████████████████████| 173/173 [00:00<00:00, 54146.30files/s]
copying 173 files..
100%|██████████████████████████████████████████████| 552M/552M [00:06<00:00, 97.6MB/s, file=dk-9.4.zip]
```
