#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""saisoku_client.py
Saisoku is a Python module that helps you build complex pipelines of batch file copying jobs.

See README.md or https://github.com/shirosaidev/saisoku
for more information.

Author: shirosai <cpark16@gmail.com>

Copyright (C) Chris Park 2019-2020
saisoku is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import socket
import threading
import os
import sys
from argparse import ArgumentParser
from tqdm import tqdm
import logging


logging.basicConfig(level=logging.DEBUG)


def parse_args(args=None):
    parser = ArgumentParser(
        description=(
            'Start a Saisoku transfer client for high speed file transfers '
            'over lan or wan links.'))
    parser.add_argument(
        '-l', '--host', type=str, default=socket.gethostname(),
        help='Hostname on which server is listening on.')
    parser.add_argument(
        '-p', '--port', type=int, default=5005,
        help='Port on which to server is running on.')
    parser.add_argument(
        '-b', '--buffer', type=int, default=8192,
        help='Buffer size to use.')
    parser.add_argument(
        'filename', help='File you want to transfer.')
    return parser.parse_args(args)


def main():
    args = parse_args()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logging.info('Connecting to Saisoku transfer server on %s port %d ...' % (args.host, args.port))
        s.connect((args.host,args.port))
    except socket.error as e:
        logging.error('Socket error ' + str(e))
        sys.exit(1)

    logging.info('Transfering file %s ...' % args.filename)
    filename = os.path.basename(args.filename)
    tempfile = filename + '.part'
    try:
        s.send(args.filename.encode('utf-8'))
        data = s.recv(args.buffer)
        if data[:6] == b'EXISTS':
            filesize = int(data[6:])
            logging.info('File exists %d Bytes, downloading ...' % filesize)
            pbar = tqdm(total=filesize, unit='B', unit_scale=True, unit_divisor=1024)
            f = open(tempfile, 'wb')
            data = s.recv(args.buffer)
            f.write(data)
            totalRecv = len(data)
            while totalRecv < filesize:
                data = s.recv(args.buffer)
                f.write(data)
                dataRecv = len(data)
                totalRecv += dataRecv
                #print("{0:.2f}".format((totalRecv/float(filesize))*100)+"% Done")
                pbar.set_postfix(file=filename[-10:], refresh=False)
                pbar.update(dataRecv)
            pbar.close()
            logging.info('Download Complete!')
            f.close()
            os.rename(tempfile, filename)
        else:
            logging.info('File does not Exist!')
    except KeyboardInterrupt:
            logging.info('Download Stopped!')
    s.close()

if __name__ == '__main__':
    main()