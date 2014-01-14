#!/usr/bin/env python

import sys
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class HttpHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("content-type", "text/plain")
		self.end_headers()
		self.wfile.write(sys.argv[2])

try:
	server = HTTPServer(('', int(sys.argv[1])), HttpHandler)
	server.serve_forever()

except KeyboardInterrupt:
	server.socket.close()
