# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals

import time
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string

from django_celery_async_view.task_helpers import AbstractAsyncDownloadCreateFile, \
    AsyncViewReturnHTML


# VIEW TASK

@shared_task
def example_view_task(user_id):
    use_db = getattr(settings, 'ASYNC_VIEW_AND_DOWNLOAD_USE_DB', True)
    # Do some heavy calculations
    return AsyncViewReturnHTML(use_db=use_db).run(
        user_id=user_id,
        html_string=render_to_string(
            template_name='django_celery_async_view/after_loading.html',
            context={
                'title': 'Just an Example',
                'slow_example': False,
            },
        )
    )


@shared_task
def example_slow_view_task(user_id):
    """
    View task that takes > 15 seconds
    :param user_id:
    :return:
    """
    use_db = getattr(settings, 'ASYNC_VIEW_AND_DOWNLOAD_USE_DB', True)
    # Do some heavy calculations
    time.sleep(15)  # SLEEP
    return AsyncViewReturnHTML(use_db=use_db).run(
        user_id=user_id,
        html_string=render_to_string(
            template_name='django_celery_async_view/after_loading.html',
            context={
                'title': 'Just an Example',
                'slow_example': True,
            },
        )
    )


# DOWNLOAD FILE TASK

@shared_task()
def example_download_task(*args, **kwargs):
    use_db = getattr(settings, 'ASYNC_VIEW_AND_DOWNLOAD_USE_DB', True)
    return ExampleDownloadCreateFile(use_db=use_db).run(*args, **kwargs)


@shared_task()
def example_slow_download_task(*args, **kwargs):
    """
    Download task that takes > 15 seconds
    :param args:
    :param kwargs:
    :return:
    """
    use_db = getattr(settings, 'ASYNC_VIEW_AND_DOWNLOAD_USE_DB', True)
    time.sleep(15)  # SLEEP
    return ExampleDownloadCreateFile(use_db=use_db).run(*args, **kwargs)


class ExampleDownloadCreateFile(AbstractAsyncDownloadCreateFile):

    description = 'example_download_task'

    def create_file(self, how_many_rows):
        file_content = self.create_example_file_string(how_many_rows)
        mimetype = self.EXAMPLE_FILE_MIMETYPE
        filename = self.EXAMPLE_FILE_NAME
        return file_content, filename, mimetype

    # The following are just for this example
    EXAMPLE_FILE_MIMETYPE = 'text/plain'
    EXAMPLE_FILE_NAME = 'example-text-file.txt'

    @staticmethod
    def create_example_file_string(how_many_rows):
        file_content = ''
        row = 'This file just contains this same line {} times.\n'.format(how_many_rows)
        for i in range(how_many_rows):
            file_content += row
        return file_content
