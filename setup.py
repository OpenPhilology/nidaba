#!/usr/bin/env python

from setuptools import setup

setup(
    setup_requires=['pbr', 'nose>=1.0', 'testrepository'],
    pbr=True,
    extras_require = {
        'kraken': ['kraken>=0.3.1']
    },
)

