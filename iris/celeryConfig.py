BROKER_URL = 'redis://localhost:5001/0'
# BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'Europe/Oslo'
# CELERY_ENABLE_UTC = True
