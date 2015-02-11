from __future__ import absolute_import

from celery import Celery
from iris.config import celery_cfg

app = Celery('iris',
                include=['iris.tasks'])
app.config_from_object(celery_cfg)

if __name__ == '__main__':
    app.start()
