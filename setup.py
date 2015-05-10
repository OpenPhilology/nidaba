#!/usr/bin/env python

from setuptools import setup

setup(
    setup_requires=['pbr', 'testrepository', 'nose>=1.0', 'mock>=1.0'],
    pbr=True,
    extras_require = {
        'kraken': ['kraken>=0.3.1']
    },
)

