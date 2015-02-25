#!/usr/bin/env python

import os
import urllib2
import urlparse
import shutil
import uuid
from setuptools import setup, find_packages, Extension
from distutils.core import setup, Extension, Command
from distutils.command.install_data import install_data

manifest_url = "http://l.unchti.me/iris/MANIFEST"
download_prefix = "http://l.unchti.me/iris/"

class DownloadCommand(Command):
    description = "Download misc. data files (dictionaries, sample inputs and models for tests etc.)"
    user_options = []

    def initialize_options(self): 
        pass

    def finalize_options(self): 
        pass

    def run(self):
        print("Downloading manifest...")
        manifest = [x.strip() for x in urllib2.urlopen(manifest_url).readlines()]
        print("Downloading: ")
        for f in manifest:
            print('\t* ' + f)
            try:
                os.makedirs(os.path.dirname(f))
            except OSError:
                pass
            r = urllib2.urlopen(urlparse.urljoin(download_prefix, f))
            with open(f, 'wb') as fp:
                shutil.copyfileobj(r, fp)

setup(
    ext_modules = [Extension("iris.leper", sources=["exts/leper.c"], libraries=["lept"], extra_compile_args=["-std=c99"])],
    include_package_data=True,
    test_suite="nose.collector",
    tests_require="nose",
    setup_requires=['pbr'],
    pbr=True,
    cmdclass = {
        "download" : DownloadCommand,
    }
)
