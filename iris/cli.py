#! /usr/bin/env python
# -*- coding: utf-8 -*-
# This modul contains all entry points to the various components of iris.

from . import iris

from celery import Celery
from celery import chain
from celery import group
from celery.result import GroupResult

import sys

def main():
   print('Not implemented yet') 
