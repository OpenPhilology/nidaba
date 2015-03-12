# -*- coding: utf-8 -*-

from __future__ import absolute_import

import yaml
import sys

from os import path


def reload_config():
    """
    Triggers a global reloading of the configuration files.

    As of now configuration files are only read from sys.prefix/etc/nidaba/.
    """
    global nidaba_cfg, celery_cfg
    ipath = path.join(sys.prefix, 'etc', 'nidaba', 'nidaba.yaml')
    with open(ipath, 'rb') as fp:
        nidaba_cfg = yaml.safe_load(fp)

    cpath = path.join(sys.prefix, 'etc', 'nidaba', 'celery.yaml')
    with open(cpath, 'rb') as fp:
        celery_cfg = yaml.safe_load(fp)

reload_config()
