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
from saisoku import ThreadedCopy


class CopyFiles(luigi.Task):
    src = luigi.Parameter()
    dst = luigi.Parameter()
    threads = luigi.IntParameter(default=16)
    filelist = luigi.Parameter(default=None)
    symlinks = luigi.Parameter(default=False)
    ignore = luigi.Parameter(default=None)
    copymeta = luigi.Parameter(default=True)

    #def requires(self):
    #    return []

    #def output(self):
    #    return []

    def run(self):
        ThreadedCopy(src=self.src, dst=self.dst, threads=self.threads, filelist=self.filelist, 
                    symlinks=self.symlinks, ignore=self.ignore, copymeta=self.copymeta)


if __name__ == '__main__':
    luigi.run()
