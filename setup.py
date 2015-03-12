#!/usr/bin/env python

import os
import urllib2
import urlparse
import shutil
from setuptools import setup
from distutils.core import Extension, Command

manifest_url = "http://l.unchti.me/nidaba/MANIFEST"
download_prefix = "http://l.unchti.me/nidaba/"


class DownloadCommand(Command):
    description = "Download misc. data files (dictionaries, sample inputs and\
    models for tests etc.)"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print("Downloading manifest...")
        manifest = [x.strip() for x in
                    urllib2.urlopen(manifest_url).readlines()]
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
    ext_modules=[Extension("nidaba.leper", sources=["exts/leper.c"],
                           libraries=["lept"],
                           extra_compile_args=["-std=c99"])],
    include_package_data=True,
    test_suite="nose.collector",
    tests_require="nose",
    setup_requires=['pbr'],
    pbr=True,
    cmdclass={
        "download": DownloadCommand,
    }
)
