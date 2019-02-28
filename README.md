# Daan's Cache PoC

This cache proof of concept does not use a filesystem to store its data but uses a cyclic spool\* together with a so called history (hashtable) to store and find articles. There's a simple HTTP implementation on top of this to show its capabilities.

This PoC uses `https:///www.cloudflare.com` for any assets without a host, this is to show what would happen if you cache a whole website.
It's not even close to any quality piece of software but merely to show off what's possible without a filesystem.

## Setup
Make sure you have python3, virtualevn and pip installed, next create a new virtualenv and install the requirements:
```
virtualenv -p python3.6 venv
. venv/bin/activate
pip install -r requirements.txt
```
## Running the PoC
To run the PoC you it needs a couple of things. Two paths for the history and spool and allow to use port 8080.

The history will be created during opening, this is just a basic [Python DBM](https://docs.python.org/3.6/library/dbm.html) implementation.
The spool itself need to exists and can be a block device. If you down want to use a block device create a spool like this:
```
fallocate -l 2G /tmp/cache.spool
```
After this you can start `httppoc.py`. Don't forget that your user needs to have access to the block device or use sudo:
```
./httppoc.py /tmp/cache.spool /tmp/cache.history
```

The server is now running and you can start caching files.

## Functions
To cache and view a file:
```
http://localhost:8080/https://www.cloudflare.com
```
Example Output:
```
The website in HTML
````

To view information about a cached file you can use the info endpoint:
```
http://localhost:8080/info/https://www.cloudflare.com
```
Example output:
```
Cache information for https://www.cloudflare.com

Cached file header:
Magic: 0xaabbccdd
Created: Thu Feb 28 08:34:08 2019 (1551314048.0)
CRC: 0x6a989019
Size: 130.4 kB (130371 bytes)
Spool position: 1

Spool header:
Magic: 0xcf1337cf
Version: 1
Created: Thu Feb 28 08:32:00 2019 (1551313920.0)
Updated: Thu Feb 28 08:32:57 2019 (1551313977.7210858)
Next Spool position: 338

Spool info:
Path: /tmp/cache.spool
Block size: 8192
Spool size: 2.1 GB (2147483648 bytes)
````
To purge a cache asset:
```
curl -XPATCH http://localhost:8080/https://www.cloudflare.com
```
Example output:
```
URL https://www.cloudflare.com has been purged from cache.
```
To purge all the cache:
```
curl -XPATCH http://localhost:8080/all
```
Example output:
```
All cache has been purged
```
