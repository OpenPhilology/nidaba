#!/usr/bin/env python

from setuptools import setup


import os

# override default requirements file
os.environ['PBR_REQUIREMENTS_FILES'] = "requirements_client.txt"

setup(
    setup_requires=['pbr', 'testrepository', 'nose>=1.0', 'mock>=1.0'],
    pbr='setup_client.cfg',
)

