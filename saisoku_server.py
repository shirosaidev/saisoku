#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""saisoku_server.py
Saisoku is a Python module that helps you build complex pipelines of batch file copying jobs.

See README.md or https://github.com/shirosaidev/saisoku
for more information.

Author: shirosai <cpark16@gmail.com>

Copyright (C) Chris Park 2019
saisoku is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import socket
import threading
import os
import sys
import time
from argparse import ArgumentParser
import logging
from saisoku import output_banner


logging.basicConfig(level=logging.DEBUG)


def RetrFile(name, sock, buff):
    filename = sock.recv(buff).decode('utf-8')
    logging.debug("client requested file:<" + str(filename) + ">")
    if os.path.isfile(filename):
        s = "EXISTS " + str(os.path.getsize(filename))
        sock.send(s.encode('utf-8'))
        with open(filename, 'rb') as f:
            bytesToSend = f.read(buff)
            sock.send(bytesToSend)
            while bytesToSend != "":
                bytesToSend = f.read(buff)
                sock.send(bytesToSend)
        f.close()
    else:
        sock.send(b"ERR")
    sock.close()


def parse_args(args=None):
    parser = ArgumentParser(
        description=(
            'Start a Saisoku transfer server for high speed file transfers '
            'over lan or wan links.'))
    parser.add_argument(
        '-l', '--host', type=str, default=socket.gethostname(),
        help='Hostname to listen on.')
    parser.add_argument(
        '-p', '--port', type=int, default=5005,
        help='Port on which to run server.')
    parser.add_argument(
        '-c', '--listen', type=int, default=5,
        help='Numbers of allowed client connections.')
    parser.add_argument(
        '-b', '--buffer', type=int, default=8192,
        help='Buffer size to use.')
    parser.add_argument(
        '-t', '--httpserver', action='store_true',
        help='Start a Tornado http server to serve static files out of a '
            'given directory.')
    parser.add_argument(
        '-d', '--dir', help='Directory from which to serve files for http.')
    return parser.parse_args(args)


def main():
    args = parse_args()

    if args.httpserver:
        import tserv

        tserv.start_http_server(args)

    else:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((args.host,args.port))
            s.listen(args.listen)
        except socket.error as e:
            logging.error('Socket error ' + str(e))
            sys.exit(1)

        logging.info('Saisoku transfer server running on %s port %d ...' % (args.host, args.port))

        try:
            while True:
                c, addr = s.accept()
                logging.debug("client connected ip:<" + str(addr) + ">")
                t = threading.Thread(target=RetrFile, args=("retrThread", c, args.buffer))
                t.start()
        except KeyboardInterrupt:
            logging.info('Stopped!')

        s.close()

if __name__ == '__main__':
    output_banner()
    main()