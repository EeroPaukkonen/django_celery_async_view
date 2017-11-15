#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from mock import patch

try:
    from django.urls import reverse
except ImportError:
    # Deprecated and removed RemovedInDjango20Warning
    from django.core.urlresolvers import reverse
from django_celery_async_view.models import TempFile
from django.test import override_settings

from example.tasks import ExampleDownloadCreateFile, example_download_task
from example.tests.test_utils import CeleryTestCase
from example.views import ExampleDownloadView
from example.tests.test_utils import CeleryTestCaseNoDBMixin

from http.client import FORBIDDEN


class BaseTestAsyncDownload(CeleryTestCase):

    expected_tempfile_description = 'example_download_task'

    def _test_get_async_download(self, user=None, expected_to_be_deleted_count=0):
        original_tempfile_count = TempFile.objects.count()
        original_tempfile_ids = list(TempFile.objects.all().values_list('id', flat=True))
        # Phase 1. Start creating file
        task_id = self.phase1_start_creating_file()
        # Phase 2. Is file ready
        self.phase2_is_file_ready(
            task_id, user, original_tempfile_count, original_tempfile_ids,
            expected_to_be_deleted_count
        )
        # Phase 3. Get file
        self.phase3_get_file(task_id)
        return task_id

    def phase1_start_creating_file(self):
        response = self.client.get(self.example_download_url)
        # TEST response
        self.assertEqual(response.status_code, 200)
        content = self.assertIsJSON(response.content)
        self.assertIn('task_id', content)
        self.assertIn('ready', content)
        self.assertFalse(content['ready'])
        task_id = content['task_id']
        return task_id

    def phase2_is_file_ready(self, task_id, user,
                             original_tempfile_count, original_tempfile_ids,
                             expected_to_be_deleted_count):
        # wait the example_download_task has finished
        example_download_task.AsyncResult(task_id).wait(timeout=5, interval=0.5)
        # request
        response = self.client.get(
            self.example_download_url, {
                'task_id': task_id
            })
        # TEST response
        self.assertEqual(response.status_code, 200)
        content = self.assertIsJSON(response.content)
        self.assertIn('ready', content)
        self.assertTrue(content['ready'])
        # Test tempfiles (if use_db)
        self.assert_temp_files(
            user, original_tempfile_count,
            original_tempfile_ids, expected_to_be_deleted_count)

    def phase3_get_file(self, task_id=None, success=True, no_http_params=False):
        """

        :param task_id:
        :param success:
        :param no_http_params: True used in eager test
        :return:
        """
        if no_http_params:
            http_params = {}
        else:
            http_params = {
                'task_id': task_id,
                'download': True
            }
        response = self.client.get(
            self.example_download_url,
            http_params
        )
        # TEST response
        if success:
            # SUCCESS
            self.assertEqual(response.status_code, 200)
            self.assertEquals(
                response.get('Content-Type'),
                ExampleDownloadCreateFile.EXAMPLE_FILE_MIMETYPE
            )
            self.assertEquals(
                response.get('Content-Disposition'),
                u'attachment; filename={}'.format(ExampleDownloadCreateFile.EXAMPLE_FILE_NAME)
            )
            # Does the file returned contain what we expect
            expected_file_content = \
                ExampleDownloadCreateFile.create_example_file_string(
                    ExampleDownloadView.HOW_MANY_ROWS)
            self.assertEquals(response.content, expected_file_content)
        else:
            # FAIL
            self.assertEqual(response.status_code, FORBIDDEN)
            #  django.views.defaults.permission_denied
            self.assertEquals(response.content, '<h1>403 Forbidden</h1>')

    @property
    def example_download_url(self):
        return reverse('example_download')


class TestAsyncDownload(BaseTestAsyncDownload):

    def test_not_logged_in(self):
        """
        Get file as anonymous user.
        Test that creating 2 files creates 2 in database.
        """
        original_tempfile_count = TempFile.objects.count()
        self._test_get_async_download()
        self._test_get_async_download()
        self.assert_tempfile_count_change(
            original_tempfile_count, 2)

    def test_logged_in(self):
        """
        1) Get file as user1
        2) Fail getting the user1's file with "stolen" task_id as anonymous user
        3) Fail getting the user1's file with "stolen" task_id as user2
        4) Still able to get the file as user1
        """
        # 1) Get file as user1
        login_success = self.client.login(username=self.username1, password=self.password1)
        self.assertTrue(login_success)
        task_id = self._test_get_async_download(user=self.user1)

        # 2) Fail getting the user1's file with "stolen" task_id as anonymous user
        self.client.logout()
        self.phase3_get_file(task_id, success=False)

        # 3) Fail getting the user1's file with "stolen" task_id as user2
        # login user2
        login_success = self.client.login(username=self.username2, password=self.password2)
        self.assertTrue(login_success)
        self.phase3_get_file(task_id, success=False)

        # 4) Still able to get the file as user1
        # login user1
        login_success = self.client.login(username=self.username1, password=self.password1)
        self.assertTrue(login_success)
        self.phase3_get_file(task_id, success=True)


@override_settings(ASYNC_VIEW_TEMP_FILE_DURATION_MS=0)
class TestAsyncDownload_TEMP_FILE_DURATION_MS0(BaseTestAsyncDownload):

    def test_delete_file_after(self):
        """
        We test that the tempfiles are actually deleted.
        Having 0ms life is just for testing.
        Old files are deleted when new tempfile is created.
        :return:
        """
        original_tempfile_count = TempFile.objects.count()
        self._test_get_async_download()
        self.assert_tempfile_count_change(
            original_tempfile_count, 1, '(1 created nothing deleted yet) ')
        self._test_get_async_download(expected_to_be_deleted_count=1)
        self.assert_tempfile_count_change(
            original_tempfile_count, 1, '(1 of the new was deleted) ')
        # delete the remaining TempFile
        TempFile.objects.delete_old_files()
        self.assert_tempfile_count_change(
            original_tempfile_count, 0, '(all deleted from the original state) ')


@override_settings(ASYNC_VIEW_AND_DOWNLOAD_USE_DB=False)
class TestAsyncDownload_NoDB(CeleryTestCaseNoDBMixin, TestAsyncDownload):
    pass


class TestAsyncDownload_EAGER(BaseTestAsyncDownload):
    """
    The file is downloaded with one call
    """
    def test_eager(self):
        with patch('example.views.ExampleDownloadView.eager', True):
            self.assertEqual(ExampleDownloadView.eager, True)
            self.phase3_get_file(no_http_params=True)
        self.assertEqual(ExampleDownloadView.eager, False)
