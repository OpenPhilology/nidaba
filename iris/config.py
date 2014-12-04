# -*- coding: utf-8 -*-

import yaml
import sys

from os import path

ipath = path.join(sys.prefix, 'etc', 'iris', 'iris.yaml')
with open(ipath, 'rb') as fp:
    iris_cfg = yaml.safe_load(fp)

cpath = path.join(sys.prefix, 'etc', 'iris', 'celery.yaml')
with open(cpath, 'rb') as fp:
    celery_cfg = yaml.safe_load(fp)
