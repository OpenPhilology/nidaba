# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, absolute_import

import yaml
import sys
import redis

from os import path

from nidaba.nidabaexceptions import NidabaConfigException


def reload_config():
    """
    Triggers a global reloading of the configuration files and reinitializes
    the redis connection pool.

    As of now configuration files are only read from sys.prefix/etc/nidaba/.
    """
    global nidaba_cfg, celery_cfg, Redis
    ipath = path.join(sys.prefix, 'etc', 'nidaba', 'nidaba.yaml')
    with open(ipath, 'rb') as fp:
        nidaba_cfg = yaml.safe_load(fp)
    if 'redis_url' not in nidaba_cfg:
        raise NidabaConfigException('No redis URL defined')
    Redis = redis.from_url(nidaba_cfg['redis_url'])

    cpath = path.join(sys.prefix, 'etc', 'nidaba', 'celery.yaml')
    with open(cpath, 'rb') as fp:
        celery_cfg = yaml.safe_load(fp)

reload_config()
