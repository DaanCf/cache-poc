#!/usr/bin/env python3
from cache import *
from socketserver import TCPServer
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse
import sys, os, re, time, humanize

cache = Cacher(sys.argv[1], sys.argv[2]) 

PORT = 8080

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if self.path == '/metrics':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Metrics endpoint')
            return
        if re.match(r'^/info', self.path):
            # Show info about the cached file, if available.
            cacheUrl = self.path.split('/',2)[2]
            # Dirty yadayada
            if cacheUrl[:4] != 'http':
                cacheUrl = 'https://www.cloudflare.com/' + cacheUrl
            if not cache.inCache(cacheUrl): 
                self.send_response(200)
                self.end_headers()
                self.wfile.write('{} is not in cache.\n'.format(cacheUrl).encode())
                return
            spoolHeader, articleHeader, spoolPosition = cache.getInfo(cacheUrl)
            articleHeader = articleHeader[1]
            parts = [
                'Cache information for {}'.format(cacheUrl),
                '',
                'Cached file header:',
                'Magic: {}'.format(hex(articleHeader.magic)),
                'Created: {} ({})'.format(time.ctime(articleHeader.created), articleHeader.created),
                'CRC: {}'.format(hex(articleHeader.crc)),
                'Size: {} ({} bytes)'.format(humanize.naturalsize(articleHeader.length), articleHeader.length),
                'Spool position: {}'.format(spoolPosition),
                '',
                'Spool header:',
                'Magic: {}'.format(hex(spoolHeader.magic)),
                'Version: {}'.format(spoolHeader.version),
                'Created: {} ({})'.format(time.ctime(spoolHeader.created), spoolHeader.created),
                'Updated: {} ({})'.format(time.ctime(spoolHeader.updated), spoolHeader.updated),
                'Next Spool position: {}'.format(spoolHeader.curpos),
                '',
                'Spool info:',
                'Path: {}'.format(cache.spool.spoolFile),
                'Block size: {}'.format(cache.spool.BLKSIZE),
                'Spool size: {} ({} bytes)'.format(humanize.naturalsize(cache.spool.spoolSize), cache.spool.spoolSize),
            ]
            self.send_response(200)
            self.end_headers()
            self.wfile.write('\r\n'.join(parts).encode())
            return

    
        # Here we do the caching!
        cacheUrl = self.path.strip('/')

        # If we don't specify host, assume https://www.cloudflare.com
        if cacheUrl[:4] != 'http':
            cacheUrl = 'https://www.cloudflare.com/' + cacheUrl
        
        if not cache.inCache(cacheUrl):
            cacheStatus, cacheMessage = cache.cacheFile(cacheUrl, self.headers)
            if not cacheStatus:
                self.send_response(500)
                self.end_headers()
                self.wfile.write('Unable to cache {}, reason: {}\n'.format(cacheUrl, cacheMessage).encode())
                return
                    
        cacheStatus, cacheHeaders, cacheBody = cache.getFile(cacheUrl)

        if not cacheStatus:
            self.send_response(500)
            self.end_headers()
            self.wfile.write('Unable to retrieve "{}" from cache, reason: {}\n'.format(cacheUrl, cacheHeaders).encode())
            return
 
        self.send_response(200)
        for name, value in cacheHeaders.items():
            if name.lower() in ['content-type', 'content-length']:
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(cacheBody)
        return

    def do_PATCH(self):
        parsed_path = urlparse(self.path)
        if self.path == '/all':
            cache.purgeCache()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'All cache has been purged')
            return

        cacheUrl = self.path.strip('/')
        cache.purgeCache(cacheUrl)
        self.send_response(200)
        self.end_headers()
        self.wfile.write('URL {} has been purged from cache.'.format(cacheUrl).encode())
        return


with TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
