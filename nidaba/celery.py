from __future__ import unicode_literals, print_function, absolute_import

from celery import Celery
from nidaba.config import celery_cfg

app = Celery('nidaba',
             include=['nidaba.tasks'])
app.config_from_object(celery_cfg)

if __name__ == '__main__':
    app.start()
