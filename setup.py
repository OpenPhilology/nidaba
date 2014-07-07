#!/usr/bin/env python

import os
import glob
from pip.req import parse_requirements
from setuptools import setup, find_packages, Extension

# retains all data from the share directory 
datadir = 'share'
walker = os.walk(datadir)
datafiles = [(w[0], [os.path.join(w[0], f) for f in w[2]]) for w in walker]

# All hail the pip-ian way of doing things
install_reqs = parse_requirements('requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name = "iris",
    description = "The OCR pipeline to succeed Rigaudon",
    packages = find_packages(exclude=['tests']),
    data_files = datafiles,
    ext_modules = [Extension("leper", sources=["exts/leper.c"], libraries=["lept"], extra_compile_args=["-std=c99"])],
    include_package_data=True,
    test_suite="nose.collector",
    tests_require="nose",
    install_requires=reqs,
    zip_safe = False,
)
