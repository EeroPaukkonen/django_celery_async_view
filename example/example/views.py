# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals
from django_celery_async_view.views import AbstractAsyncView, AsyncDownloadView
from example.tasks import example_view_task, example_download_task, \
    example_slow_view_task, example_slow_download_task


class ExampleView(AbstractAsyncView):
    loading_page_template = 'django_celery_async_view/loading.html'
    task = example_view_task
    context = {}


class ExampleSlowView(AbstractAsyncView):
    loading_page_template = 'django_celery_async_view/loading.html'
    task = example_slow_view_task
    context = {}


class ExampleDownloadView(AsyncDownloadView):

    task = example_download_task
    allow_no_user = True

    # Example variable. here just for testing
    HOW_MANY_ROWS = 4

    def setup(self, request):
        self.create_file_kwargs = {
            'how_many_rows': self.HOW_MANY_ROWS,
        }


class ExampleSlowDownloadView(ExampleDownloadView):
    task = example_slow_download_task
