# -*- coding: utf-8 -*-

from __future__ import absolute_import

import yaml
import sys

from os import path

def reload_config():
    global iris_cfg, celery_cfg
    ipath = path.join(sys.prefix, 'etc', 'iris', 'iris.yaml')
    with open(ipath, 'rb') as fp:
        iris_cfg = yaml.safe_load(fp)

    cpath = path.join(sys.prefix, 'etc', 'iris', 'celery.yaml')
    with open(cpath, 'rb') as fp:
        celery_cfg = yaml.safe_load(fp)

reload_config()
