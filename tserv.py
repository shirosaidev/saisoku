#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tsver.py
Saisoku is a Python module that helps you build complex pipelines of batch file copying jobs.

tserv how to

Starts a Tornado static file server in a given directory.
To start the server in the current directory:
    tserv .
Then go to http://localhost:8000 to browse the directory.
Use the --prefix option to add a prefix to the served URL,
for example to match GitHub Pages' URL scheme:
    tserv . --prefix=saisoku
Then go to http://localhost:8000/saisoku/ to browse.
Use the --port option to change the port on which the server listens.

Author: shirosai <cpark16@gmail.com>

Copyright (C) Chris Park 2019
saisoku is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from __future__ import print_function
import os
import sys
from argparse import ArgumentParser
from scandir import scandir
import tornado.ioloop
import tornado.web
import tornado.options
tornado.options.parse_command_line()


class Handler(tornado.web.StaticFileHandler):
    def parse_url_path(self, url_path):
        if not url_path or url_path.endswith('/'):
            url_path = url_path + 'index.html'
        return url_path


def mkapp(prefix=''):
    if prefix:
        path = '/' + prefix + '/(.*)'
    else:
        path = '/(.*)'
    application = tornado.web.Application([
        (path, Handler, {'path': os.getcwd()}),
    ], debug=True)
    return application


def start_server(prefix='', port=8000):
    app = mkapp(prefix)
    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()


def create_index(d):
    with open('index.html', 'w') as f:
        for item in scandir(d):
            if item.is_file():
                f.write('<a title="' + str(item.stat().st_size) + '" href="' + item.name + '">' + item.name + '</a><br>\n')


def parse_args(args=None):
    parser = ArgumentParser(
        description=(
            'Start a Tornado server to serve static files out of a '
            'given directory and with a given prefix.'))
    parser.add_argument(
        '-f', '--prefix', type=str, default='',
        help='A prefix to add to the location from which pages are served.')
    parser.add_argument(
        '-p', '--port', type=int, default=8000,
        help='Port on which to run server.')
    parser.add_argument(
        'dir', help='Directory from which to serve files.')
    return parser.parse_args(args)


def main():
    args = parse_args()
    os.chdir(args.dir)
    print('Starting server on port {}'.format(args.port))
    create_index(args.dir)
    try:
        start_server(prefix=args.prefix, port=args.port)
    except KeyboardInterrupt:
        print('Stopping server..')


if __name__ == '__main__':
    main()