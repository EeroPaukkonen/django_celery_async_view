#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import re

from django.template.loader import render_to_string
from django.test import override_settings
from mock import patch

try:
    from django.urls import reverse
except ImportError:
    # Deprecated and removed RemovedInDjango20Warning
    from django.core.urlresolvers import reverse

from example.tasks import example_view_task
from example.tests.test_utils import CeleryTestCase
from example.tests.test_utils import CeleryTestCaseNoDBMixin
from example.views import ExampleView

from http.client import FORBIDDEN

from django_celery_async_view.models import TempFile


class BaseTestAsyncViews(CeleryTestCase):
    expected_tempfile_description = ''
    task_id_pattern = re.compile(r"var\stask_id\s=\s'([-|\w]+)';")

    def _test_get_async_view(self, user=None, expected_to_be_deleted_count=0):
        original_tempfile_count = TempFile.objects.count()
        original_tempfile_ids = list(TempFile.objects.all().values_list('id', flat=True))
        # Phase 1.
        task_id = self.phase1()
        # Phase 3.
        self.phase3(task_id, user,
                    original_tempfile_count, original_tempfile_ids,
                    expected_to_be_deleted_count)

    def phase1(self):
        response = self.client.get(self.example_view_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_celery_async_view/loading.html')
        # get task_id from the html
        task_ids = self.task_id_pattern.findall(response.content.decode('utf-8'))
        self.assertEqual(1, len(task_ids))
        task_id = task_ids[0]
        self.assertTrue(len(task_id) > 0)
        return task_id

    def phase3(self, task_id, user,
               original_tempfile_count, original_tempfile_ids,
               expected_to_be_deleted_count, success=True):
        example_view_task.AsyncResult(task_id).wait(timeout=5, interval=0.5)
        # request
        response = self.client.get(
            self.example_view_url, {
                'task_id': task_id
            })
        # TEST response
        if success:
            self.assertEqual(response.status_code, 200)
            content = self.assertIsJSON(response.content)
            self.assertIn('ready', content)
            self.assertTrue(content['ready'])
            self.assertIn('html', content)
            self.assert_async_view_html(content['html'])
            # Test tempfiles (if use_db)
            self.assert_temp_files(
                user, original_tempfile_count,
                original_tempfile_ids, expected_to_be_deleted_count)
        else:
            # FAIL
            self.assertEqual(response.status_code, FORBIDDEN)

    def assert_async_view_html(self, html):
        self.assertEqual(
            html,
            render_to_string(
                template_name='django_celery_async_view/after_loading.html',
                context={
                    'title': 'Just an Example'
                }, )
        )

    @property
    def example_view_url(self):
        return reverse('example_view')


class TestAsyncViews(BaseTestAsyncViews):

    def test_get_async_view(self):
        self._test_get_async_view()


@override_settings(ASYNC_VIEW_AND_DOWNLOAD_USE_DB=False)
class TestAsyncViews_NoDB(CeleryTestCaseNoDBMixin, TestAsyncViews):
    pass


class TestAsyncViews_EAGER(BaseTestAsyncViews):
    """
    The file is downloaded with one call
    """
    def test_eager(self):
        with patch('example.views.ExampleView.eager', True):
            self.assertEqual(ExampleView.eager, True)

            response = self.client.get(self.example_view_url)
            self.assertEqual(response.status_code, 200)
            self.assert_async_view_html(response.content)

        self.assertEqual(ExampleView.eager, False)
