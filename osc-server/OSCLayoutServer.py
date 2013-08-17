"""Simple HTTP Server.

This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

"""


__version__ = "0.6"

import os
import posixpath
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import urllib
import cgi
import sys
import shutil
import time
import mimetypes
import zipfile
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

filename = 'amcp_template.touchosc'

def doit(filename):
    class OSCRequestHandler(SimpleHTTPRequestHandler):

        """OSCRequestHandler

        Hardcode the information necessary for TouchOSC to download the supplied
        layout file.

        """

        def send_head(self):
            """Hard coded single-file server.
            """
            self.send_response(200)
            self.send_header("Content-type", 'application/touchosc')
            self.send_header("Date", self.date_time_string(time.time()))
            self.send_header("Content-Disposition", 'attachment; filename="%s"' %
                (filename, ))
            self.end_headers()
            full_filename = os.path.join(os.path.dirname(__file__), filename)
            z = zipfile.ZipFile(full_filename)
            return z.open('index.xml', 'r')
    server_address = ('', 9658)
    httpd = BaseHTTPServer.HTTPServer(server_address, OSCRequestHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    doit(sys.argv[1])
