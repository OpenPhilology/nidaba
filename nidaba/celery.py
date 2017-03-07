from __future__ import unicode_literals, print_function, absolute_import

from celery import Celery
from celery import chain
from celery import group
from nidaba.config import celery_cfg
app = Celery('nidaba',
             strict_typing=False,
             include=['nidaba.tasks'])
app.config_from_object(celery_cfg)
from nidaba import plugins

if __name__ == '__main__':
    app.start()
