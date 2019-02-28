from spool import *
from history import *
import requests
import hashlib
import re
import json

class Cacher:

    def __init__(self, spoolFile, historyFile):
        self.spool = Spool(spoolFile)
        self.history = History(historyFile)
        if not self.spool.openSpool():
            self.spool.formatSpool()
            self.spool.openSpool()
        self.history.openHistory()

    def cacheFile(self, url, headers={}):
        # Quick an dirty to remove invalid headers
        print('Caching {}'.format(url))
        newHeaders = {}
        for name, value in sorted(headers.items()):
            if name.lower() not in ['host', 'accept-encoding']:
                newHeaders[name] = value
        try:
            r = requests.get(url, headers=newHeaders, timeout=15, allow_redirects=False)
        except requests.exceptions.RequestException as e:
            return False, e
        m = hashlib.sha256()
        m.update(url.encode())
        # Only cache 2xx statussen
        if not re.match(r"^2[0-9]{2}$", str(r.status_code)):
            return False, 'Not a 2xx respone from orign: {}'.format(r.status_code)
        headers = json.dumps(dict(r.headers))
        content = r.content
        
        startpos, artpos, written, newpos = self.spool.writeData(headers.encode() + b'---HEADBODY---' + content)
        self.history.setPos(m.digest(), artpos)
        
        return True, 'Cached'

    def inCache(self, url):
        m = hashlib.sha256()
        m.update(url.encode())
        return bool(self.history.getPos(m.digest()))
        
    def getFile(self, url):
        print('Get {} from cache'.format(url))
        m = hashlib.sha256()
        m.update(url.encode())
        if not self.inCache(url):
            return False, 'File not in cache', ''
        
        status, data = self.spool.readData(self.history.getPos(m.digest()))
        if not status:
            return False, 'Unable to load file from cache', ''
        headers, body = data.split(b'---HEADBODY---', 1)
        return True, json.loads(headers.decode()), body

    def getInfo(self, url):
        m = hashlib.sha256()
        m.update(url.encode())
        if not self.inCache(url):
            return False, 'Not in cache', '', ''
        return self.spool.getSpoolHeader(), self.spool.getArticleHeader(self.history.getPos(m.digest())), self.history.getPos(m.digest())
        
    def purgeCache(self, url=None):
        if url is None:
            print('Purging all cache.')
            self.history.delAll()
            return True
        m = hashlib.sha256()
        m.update(url.encode())
        print ('Purging {} from cache.'.format(url))
        self.history.delPos(m.digest())
        return True
