import os
import struct
import math
import binascii
import dbm

class History:

    def __init__(self, historyFile):
        self.historyFile = historyFile

    def openHistory(self):
        self.db = dbm.open(self.historyFile, 'cf')

    def setPos(self, cacheHash, filePos):
        self.db[cacheHash] = bin(filePos)
        return True

    def getPos(self, cacheHash):
        if cacheHash not in self.db:
            return False
        return int(self.db[cacheHash], 2)

    def closeHistory(self):
        self.db.close()

    def delPos(self, cacheHash):
        try:
            del self.db[cacheHash]
        except KeyError:
            pass
        return

    def delAll(self):
        self.closeHistory()
        self.db = dbm.open(self.historyFile, 'nf')
