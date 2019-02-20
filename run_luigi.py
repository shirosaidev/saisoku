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

    def run(self):
        ThreadedCopy(src=self.src, dst=self.dst, threads=self.threads, filelist=self.filelist, 
                    symlinks=self.symlinks, ignore=self.ignore, copymeta=self.copymeta)

    #def output(self):
        #    return []


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


if __name__ == '__main__':
    luigi.run()
