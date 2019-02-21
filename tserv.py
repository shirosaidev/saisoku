#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""tsver.py
Saisoku is a Python module that helps you build complex pipelines of batch file copying jobs.

Author: shirosai <cpark16@gmail.com>

Copyright (C) Chris Park 2019
saisoku is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

"""
Starts a Tornado static file server in a given directory.
To start the server in the current directory:
    tserv .
Then go to http://localhost:8000 to browse the directory.
Use the --port option to change the port on which the server listens.
"""

import os
import sys
from argparse import ArgumentParser
from scandir import scandir
import logging
import signal

import tornado.ioloop
import tornado.web
import tornado.template
import tornado.httpserver


logging.basicConfig(level=logging.DEBUG)


class IndexHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, path):
        """ GET method to list contents of directory or
        write index page if index.html exists."""

        # remove heading slash
        path = path[1:]

        for index in ['index.html', 'index.htm']:
            index = os.path.join(path, index)
            if os.path.exists(index):
                with open(index, 'rb') as f:
                    self.write(f.read())
                    self.finish()
                    return
        html = self.generate_index(path)
        self.write(html)
        self.finish()

    def generate_index(self, path):
        """ generate index html page, list all files and dirs.
        """
        if path:
            files = [item for item in scandir(path)]
        else:
            files = [item for item in scandir('.')]
        files = [(item.name + '/', 0) if item.is_dir() else (item.name, str(item.stat().st_size)) for item in files]
        html_template = """
        <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>
        <title>Directory listing for /{{ path }}</title>
        <body>
        <h2>Directory listing for /{{ path }}</h2>
        <hr>
        <ul>
        {% for filename, size in files %}
        <li><a title="{{ size }}" href="{{ filename }}">{{ filename }}</a>
        {% end %}
        </ul>
        <hr>
        </body>
        </html>
        """
        t = tornado.template.Template(html_template)
        return t.generate(files=files, path=path)


class StaticFileHandler(tornado.web.StaticFileHandler):
    
    def write(self, chunk):
        super(StaticFileHandler, self).write(chunk)
        #logging.debug('write called')
        self.flush()


def stop_server(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()
    logging.info('Stopped!')


def parse_args(args=None):
    parser = ArgumentParser(
        description=(
            'Start a Tornado server to serve static files out of a '
            'given directory.'))
    parser.add_argument(
        '-p', '--port', type=int, default=8000,
        help='Port on which to run server.')
    parser.add_argument(
        'dir', help='Directory from which to serve files.')
    return parser.parse_args(args)


def main():
    args = parse_args()
    os.chdir(args.dir)
    logging.debug('cwd: %s' % args.dir)
    try:
        application = tornado.web.Application([
        (r'(.*)/$', IndexHandler,),
        (r'/(.*)$', StaticFileHandler, {'path': args.dir}),
        ])
        signal.signal(signal.SIGINT, stop_server)

        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(args.port)
        logging.info('Starting HTTP server on 0.0.0.0 port %d ...' % args.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, stop_server)


if __name__ == '__main__':
    main()