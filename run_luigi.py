#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""run_luigi.py
Saisoku is a Python module that helps you build complex pipelines of batch file copying jobs.

Author: shirosai <cpark16@gmail.com>

Copyright (C) Chris Park 2019
saisoku is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import luigi
from saisoku import ThreadedCopy, ThreadedHTTPCopy
import logging


logging.basicConfig(level=logging.DEBUG)


class CopyFiles(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()
    threads = luigi.IntParameter(default=16)
    filelist = luigi.OptionalParameter(default=None)
    symlinks = luigi.BoolParameter(default=False)
    ignore = luigi.OptionalParameter(default=None)
    copymeta = luigi.BoolParameter(default=True)

    #def requires(self):
    #    return []

    #def output(self):
    #    return []

    def run(self):
        ThreadedCopy(src=self.src, dst=self.dst, threads=self.threads, filelist=self.filelist, 
                    symlinks=self.symlinks, ignore=self.ignore, copymeta=self.copymeta)


class CopyFilesHTTP(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()
    threads = luigi.IntParameter(default=16)
    tservports = luigi.ListParameter(default=[8000,8001,8002,8003])
    fetchmode = luigi.Parameter(default='urlretrieve')
    chunksize = luigi.IntParameter(default=16384)

    def run(self):
        ThreadedHTTPCopy(src=self.src, dst=self.dst, threads=self.threads, tservports=self.tservports, 
                    fetchmode=self.fetchmode, chunksize=self.chunksize)


class PackageDirectory(luigi.Task):
    src = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget('saisoku_filelist.txt')

    def run(self):
        import tarfile
        from scandir import scandir
        import os

        archives = []
        src_path = os.path.abspath(self.src)
        # create tar.gz of all files in directory
        archive_name = '{}_saisoku_archive.tar.gz'.format(os.path.basename(src_path))
        logging.info('Compressing files to %s...' % archive_name)
        tar = tarfile.open(archive_name, "w:gz")
        for item in scandir(self.src):
            if item.is_file():
                logging.debug('  Adding %s...' % item.name)
                tar.add(item.path, item.name)
        tar.close()
        archives.append(archive_name)

        with self.output().open('w') as f:
            for archive in archives:
                f.write('{archive}\n'.format(archive=archive))


class CopyFilesPackage(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()
    threads = luigi.IntParameter(default=16)
    filelist = 'saisoku_filelist.txt'
    symlinks = luigi.BoolParameter(default=False)
    ignore = luigi.OptionalParameter(default=None)
    copymeta = luigi.BoolParameter(default=True)

    def requires(self):
        return [PackageDirectory(src=self.src)]

    def run(self):
        ThreadedCopy(src=self.src, dst=self.dst, threads=self.threads, filelist=self.filelist, 
                symlinks=self.symlinks, ignore=self.ignore, copymeta=self.copymeta, package=True)


if __name__ == '__main__':
    luigi.run()
