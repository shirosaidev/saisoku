#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""saisoku.py
Saisoku is a Python module that helps you build complex pipelines of batch file copying jobs.

Author: shirosai <cpark16@gmail.com>

Copyright (C) Chris Park 2019
saisoku is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import errno
import os
import time
import mmap
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
from threading import Thread, Lock
import shutil
from shutil import Error
import pyfastcopy
from scandir import scandir
from tqdm import tqdm
import logging
import tempfile


SAISOKU_VERSION = '0.1-b.1'
__version__ = SAISOKU_VERSION


# settings
logtofile = True
loglevel = logging.DEBUG


fileQueue = Queue()


def logging_setup():
    """Set up logging."""
    logger = logging.getLogger(name='saisoku')
    logger.setLevel(loglevel)
    logformatter = logging.Formatter('%(asctime)s [%(levelname)s][%(name)s] %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(loglevel)
    ch.setFormatter(logformatter)
    logger.addHandler(ch)
    logger.propagate = False
    if logtofile:
        logfile = os.path.join(tempfile.gettempdir(), 'saisoku.log')
        hdlr = logging.FileHandler(logfile)
        hdlr.setLevel(loglevel)
        hdlr.setFormatter(logformatter)
        logger.addHandler(hdlr)
    return logger

logger = logging_setup()


class ThreadedCopy:
    """Threaded file copy class."""
    totalFiles = 0
    copyCount = 0
    lock = Lock()

    def __init__(self, src, dst, threads=16, filelist=None, symlinks=False, ignore=None, copymeta=True):
        self.src = src
        self.dst = dst
        self.threads = threads
        self.filelist = filelist
        self.symlinks = symlinks
        self.ignore = shutil.ignore_patterns(ignore)  # copytree ignore patterns like ('*.pyc', 'tmp*')
        self.copymeta = copymeta
        self.fileList = []
        self.sizecounter = 0
        self.errors = []

        logger.info('Starting file copy from %s to %s..' % (self.src, self.dst))

        # open filelist txt file or scandir src path and preprocess the total files sizes
        logger.info("Calculating total file size..")
        if filelist:
            with open(self.filelist, "r") as file:  # txt with a file per line
                for line in tqdm(file, total=self.get_num_lines(self.filelist), unit='files'):
                    fname = line.rstrip('\n')
                    fpath = os.path.join(self.src, fname)
                    size = os.stat(fpath).st_size
                    self.fileList.append((fname, fpath, size))
                    self.sizecounter += size
        else:
            for item in tqdm(scandir(self.src), unit='files'):  # scandir and build file list
                self.fileList.append(item)
                self.sizecounter += item.stat().st_size
        # make dst directory if it doesn't exist and copy stat
        try:
            os.makedirs(dst)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(dst):
                pass
            else:
                raise
        try:
            shutil.copystat(src, dst)
        except OSError as e:
            self.errors.extend((self.src, self.dst, str(e)))
    
        self.totalFiles = len(self.fileList)
        logger.info("Copying " + str(self.totalFiles) + " files (" + str(self.sizecounter) + " bytes)..")
        self.pbar = tqdm(total=self.sizecounter, unit='B', unit_scale=True, unit_divisor=1024)
        self.threadWorkerCopy(self.fileList)


    def CopyWorker(self):
        """Thread worker for file copying."""
        while True:
            fileName = fileQueue.get()
            try:
                isdir = fileName.is_dir()  # scandir object
                issym = fileName.is_symlink()
                size = fileName.stat().st_size
                fname = fileName.name
            except AttributeError:  # file from txt
                fname, fpath, size = fileName
                isdir = True if os.path.isdir(fpath) else False
                issym = True if os.path.islink(fpath) else False
            srcname = os.path.join(self.src, fname)
            dstname = os.path.join(self.dst, fname)
            try:
                if isdir:
                    #copyf = shutil.copy2 if self.copymeta else shutil.copyfile
                    #shutil.copytree(srcname, dstname, symlinks=self.symlinks, 
                    #                ignore=self.ignore, copy_function=copyf)
                    pass
                else:
                    if issym is self.symlinks:
                        if self.copymeta:
                            try:
                                shutil.copy2(srcname, dstname)
                            except OSError as e:
                                self.errors.extend((self.src, self.dst, str(e)))
                        else:
                            shutil.copyfile(srcname, dstname)
            except OSError as e:
                self.errors.append((srcname, dstname, str(e)))
            # catch the Error from the recursive copytree so that we can
            # continue with other files
            except Error as e:
                self.errors.extend(e.args[0])
            if self.errors:
                raise Error(self.errors)
            fileQueue.task_done()
            with self.lock:
                self.copyCount += 1
                #percent = (self.copyCount * 100) / self.totalFiles
                #print(str(percent) + " percent copied.")
                self.pbar.set_postfix(file=fname[-10:], refresh=False)
                self.pbar.update(size)

    def threadWorkerCopy(self, fileNameList):
        for i in range(self.threads):
            t = Thread(target=self.CopyWorker)
            t.daemon = True
            t.start()
        for fileName in fileNameList:
            fileQueue.put(fileName)
        fileQueue.join()
        self.pbar.close()
        logger.info('Done')

    def get_num_lines(self, fileNameList):
        """Get number of lines in txt file."""
        fp = open(fileNameList, "r+")
        buf = mmap.mmap(fp.fileno(), 0)
        lines = 0
        while buf.readline():
            lines += 1
        return lines
