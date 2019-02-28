import os
from pathlib import Path
from typing import NamedTuple
import time
import struct
import math
import binascii

class SpoolHeader(NamedTuple):
    magic: int
    version: int
    created: float
    updated: float
    wrapped: int
    curpos: int

class ArticleHeader(NamedTuple):
    magic: int
    created: float
    crc: int
    length: int

class Spool:
    SPOOLMAGIC  = 0xcf1337cf
    ARTMAGIC    = 0xaabbccdd
    HEADVERSION = 1
    HEADFORMAT  = 'IHffHL'
    ARTFORMAT   = 'IfII'
    BLKSIZE     = 8192

    def __init__(self, spoolFile):
        self.spoolFile = spoolFile
        fileinfo = Path(self.spoolFile)
        fileinfo.resolve(strict=True)

    def formatSpool(self):
        self.fd = os.open(self.spoolFile, os.O_RDWR)
        
        self.spoolHeader = SpoolHeader(self.SPOOLMAGIC, self.HEADVERSION, time.time(), 0, 0, 1)
        s = struct.Struct(self.HEADFORMAT)
        self.headerSize = s.size
        self.headerPacked = s.pack(*self.spoolHeader)

        # Write the header
        os.lseek(self.fd, os.SEEK_SET, os.SEEK_SET)
        ret = os.write(self.fd, self.headerPacked)
        os.close(self.fd)

    def openSpool(self):
        self.fd = os.open(self.spoolFile, os.O_RDWR)
        self.spoolSize = os.lseek(self.fd, 0, os.SEEK_END)
        self.maxFiles = self.spoolSize / self.BLKSIZE
        # Read header
        os.lseek(self.fd, os.SEEK_SET, os.SEEK_SET)
        s = struct.Struct(self.HEADFORMAT)
        headerBytes = os.read(self.fd, s.size)
        header = s.unpack(headerBytes)
        self.spoolHeader = SpoolHeader(*header)
        if self.spoolHeader.magic != self.SPOOLMAGIC:
            return False
        return True

    def writeHeader(self):
        os.lseek(self.fd, os.SEEK_SET, os.SEEK_SET)
        s = struct.Struct(self.HEADFORMAT)
        self.headerPacked = s.pack(*self.spoolHeader)
        return os.write(self.fd, self.headerPacked)

    def updateHeader(self, updated=time.time(), wrapped=None, curpos=None):
        if wrapped is None:
            wrapped = self.spoolHeader.wrapped
        if curpos is None:
            curpos = self.spoolHeader.curpos
        self.spoolHeader = SpoolHeader(self.spoolHeader.magic, self.spoolHeader.version, self.spoolHeader.created, updated, wrapped, curpos)
        self.writeHeader()

    def writeData(self, data):
        crc = binascii.crc32(data)
        length =  len(data)
        articleHeader = ArticleHeader(self.ARTMAGIC, time.time(), crc, length)
        articlePacked = struct.pack(self.ARTFORMAT, *articleHeader)
        startpos = os.lseek(self.fd, self.BLKSIZE * self.spoolHeader.curpos, os.SEEK_SET)
        artpos = self.spoolHeader.curpos
        written = os.write(self.fd, articlePacked + data)
        newpos = math.ceil(os.lseek(self.fd, os.SEEK_CUR, os.SEEK_CUR) / self.BLKSIZE)
        self.updateHeader(curpos=newpos);
        return startpos, artpos, written, newpos

    def readData(self, pos):
        startpos = os.lseek(self.fd, self.BLKSIZE * pos, os.SEEK_SET)
        s = struct.Struct(self.ARTFORMAT)
        articleHeaderBytes = os.read(self.fd, s.size)
        articleHeader = ArticleHeader(*s.unpack(articleHeaderBytes))
        if articleHeader.magic != self.ARTMAGIC:
            return False, 'Article magic invalid'
        articleData = os.read(self.fd, articleHeader.length)
        crc = binascii.crc32(articleData)
        if articleHeader.crc != crc:
            return False, 'Article CRC mismatch'
        return True, articleData

    def getArticleHeader(self, pos):
        startpos = os.lseek(self.fd, self.BLKSIZE * pos, os.SEEK_SET)
        s = struct.Struct(self.ARTFORMAT)
        articleHeaderBytes = os.read(self.fd, s.size)
        articleHeader = ArticleHeader(*s.unpack(articleHeaderBytes))
        if articleHeader.magic != self.ARTMAGIC:
            return False, 'Article magic invalid'
        return True, articleHeader

    def getSpoolHeader(self):
        return self.spoolHeader
    
    def findArticles(self):
        print(self.spoolHeader)
        for pos in range(1, math.ceil(self.maxFiles)):
            startpos = os.lseek(self.fd, self.BLKSIZE * pos, os.SEEK_SET)
            s = struct.Struct(self.ARTFORMAT)
            articleHeaderBytes = os.read(self.fd, s.size)
            articleHeader = ArticleHeader(*s.unpack(articleHeaderBytes))
            if articleHeader.magic == self.ARTMAGIC:
                print(articleHeader)
