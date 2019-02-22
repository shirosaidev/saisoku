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
from luigi.contrib.s3 import S3Target, S3Client

import os
import time
import logging

from saisoku import logger


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


class S3File(luigi.ExternalTask):
    src = luigi.Parameter()

    def output(self):
        return S3Target(self.src)


class CopyS3FileToLocal(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(self.dst)

    def requires(self):
        return S3File(src=self.src)

    def run(self):
        """
        examples:
        * s3://bucket/foo/bar.txt
        * s3://bucket/foo/bar.txt?aws_access_key_id=xxx&aws_secret_access_key=yyy
        """
        def copy():
            with self.input().open('r') as infile:
                for line in infile:
                    yield line

        logger.info('Copying %s to %s ...' % (self.src, self.dst))
        t = time.time()
        with self.output().open('w') as outfile:
            for line in copy():
                outfile.write(line)
        t = round(time.time() - t, 2)
        size = round(os.path.getsize(self.dst) / 1024 * 1.0, 2)  # in KB
        kb_per_sec = round(size / t, 2)
        logger.info('Done. Copied %s KB in %s seconds (%s KB/s)' % (size, t, kb_per_sec))


class LocalFile(luigi.ExternalTask):
    src = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(self.src)


class CopyLocalFileToS3(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()

    def output(self):
        return S3Target(self.dst)

    def requires(self):
        return LocalFile(src=self.src)

    def run(self):
        def copy():
            with self.input().open('r') as infile:
                for line in infile:
                    yield line

        logger.info('Copying %s to %s ...' % (self.src, self.dst))
        t = time.time()
        with self.output().open('w') as outfile:
            for line in copy():
                outfile.write(line)
        t = round(time.time() - t, 2)
        size = round(os.path.getsize(self.src) / 1024 * 1.0, 2)  # in KB
        kb_per_sec = round(size / t, 2)
        logger.info('Done. Copied %s KB in %s seconds (%s KB/s)' % (size, t, kb_per_sec))


class SyncFilesRclone(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()
    flags = luigi.ListParameter(default=[])
    command = luigi.Parameter(default='sync')
    cmdargs = luigi.ListParameter(default=['--dry-run', '-vv'])

    def run(self):
        from saisoku import Rclone
        
        Rclone(src=self.src, dst=self.dst, flags=self.flags, command=self.command, cmdargs=self.cmdargs)


if __name__ == '__main__':
    luigi.run()
