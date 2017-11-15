#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from celery import Celery, VERSION

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'example.settings')

app = Celery(
    'example',
    include=[
        'example.tasks'
    ]
)

if VERSION[0] >= 4:
    # Using a string here means the worker don't have to serialize
    # the configuration object to child processes.
    # - namespace='CELERY' means all celery-related configuration keys
    #   should have a `CELERY_` prefix.
    app.config_from_object('django.conf:settings', namespace='CELERY')

    # Load task modules from all registered Django app configs.
    app.autodiscover_tasks()
else:
    from django.conf import settings  # noqa
    # Using a string here means the worker will not have to
    # pickle the object when using Windows.
    app.config_from_object('django.conf:settings')
    app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
