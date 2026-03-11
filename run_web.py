"""
Helper script to run pygbag with SSL verification disabled.
This is needed on some Windows machines where SSL certificates
are not properly configured (e.g., corporate/school networks).
"""
import ssl
import sys
import os

# Disable SSL verification globally BEFORE importing anything else
ssl._create_default_https_context = ssl._create_unverified_context

# Also patch urllib to not verify SSL
import urllib.request
original_urlretrieve = urllib.request.urlretrieve

def patched_urlretrieve(url, filename=None, reporthook=None, data=None):
    import urllib.request
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    urllib.request.install_opener(opener)
    return original_urlretrieve(url, filename, reporthook, data)

urllib.request.urlretrieve = patched_urlretrieve

# Now run pygbag
sys.argv = ['pygbag', '.']

import runpy
runpy.run_module('pygbag', run_name='__main__')
