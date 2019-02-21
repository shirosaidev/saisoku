#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""run_luigi.py
Saisoku is a Python module that helps you build complex pipelines of batch file copying jobs.

See README.md or https://github.com/shirosaidev/saisoku
for more information.

Author: shirosai <cpark16@gmail.com>

Copyright (C) Chris Park 2019
saisoku is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import luigi
import logging


def logging_setup():
    """Set up logging."""
    logger = logging.getLogger(name='run_luigi')
    logger.setLevel(logging.DEBUG)
    logformatter = logging.Formatter('%(asctime)s [%(levelname)s][%(name)s] %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logformatter)
    logger.addHandler(ch)
    logger.propagate = False
    return logger

logger = logging_setup()


class CopyFiles(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()
    threads = luigi.IntParameter(default=16)
    filelist = luigi.OptionalParameter(default=None)
    symlinks = luigi.BoolParameter(default=False)
    ignore = luigi.OptionalParameter(default=None)
    copymeta = luigi.BoolParameter(default=True)

    #def output(self):
    #    return []

    #def requires(self):
    #    return []

    def run(self):
        from saisoku import ThreadedCopy
        
        ThreadedCopy(src=self.src, dst=self.dst, threads=self.threads, filelist=self.filelist, 
                    symlinks=self.symlinks, ignore=self.ignore, copymeta=self.copymeta)


class CopyFilesHTTP(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()
    threads = luigi.IntParameter(default=1)
    ports = luigi.ListParameter(default=[5005])
    fetchmode = luigi.Parameter(default='urlretrieve')
    chunksize = luigi.IntParameter(default=8192)

    def run(self):
        from saisoku import ThreadedHTTPCopy

        ThreadedHTTPCopy(src=self.src, dst=self.dst, threads=self.threads, ports=self.ports, 
                        fetchmode=self.fetchmode, chunksize=self.chunksize)


class PackageDirectory(luigi.Task):
    src = luigi.Parameter()
    filelist = luigi.Parameter(default='saisoku_filelist.txt')

    def output(self):
        return luigi.LocalTarget(self.filelist)

    def run(self):
        import tarfile
        from scandir import scandir
        import os

        archives = []
        src_path = os.path.abspath(self.src)
        # create tar.gz of all files in directory
        archive_name = '{}_saisoku_archive.tar.gz'.format(os.path.basename(src_path))
        logger.info('Compressing files to %s...' % archive_name)
        tar = tarfile.open(archive_name, "w:gz")
        for item in scandir(self.src):
            if item.is_file():
                logger.debug('  Adding %s...' % item.name)
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
    filelist = luigi.Parameter(default='saisoku_filelist.txt')
    symlinks = luigi.BoolParameter(default=False)
    ignore = luigi.OptionalParameter(default=None)
    copymeta = luigi.BoolParameter(default=True)
    cleanup = luigi.BoolParameter(default=True)

    def output(self):
        return luigi.LocalTarget(self.filelist)

    def requires(self):
        return [PackageDirectory(src=self.src, filelist=self.filelist)]

    def run(self):
        from saisoku import ThreadedCopy
        import os

        ThreadedCopy(src=self.src, dst=self.dst, threads=self.threads, filelist=self.filelist, 
                symlinks=self.symlinks, ignore=self.ignore, copymeta=self.copymeta, package=True)

        if self.cleanup:
            logger.info('Cleaning up %s...' % self.src)
            with self.input()[0].open() as f:
                filename = f.read().rstrip('\n')
                logger.debug('  Removing %s...' % filename)
                os.remove(filename)  # delete tar.gz file in src
            logger.debug('  Removing %s...' % self.filelist)
            os.remove(self.filelist)  # delete file list


if __name__ == '__main__':
    luigi.run()
