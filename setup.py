#!/usr/bin/env python

from setuptools import setup

setup(
    setup_requires=['pbr', 'testrepository', 'mock>=1.0'],
    test_suite='tests',
    pbr=True,
)

