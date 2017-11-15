#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
from celerytest.worker import CeleryWorkerThread
from celerytest.testcase import CeleryTestCaseMixin
from django.contrib.auth.models import User
from django.test import SimpleTestCase
from example.celery import app as example_celery_app

from django_celery_async_view.models import TempFile


def _start_celery_worker(app):
    # setup_celery_worker(app, config=config, concurrency=concurrency)

    worker = CeleryWorkerThread(app)
    worker.daemon = True
    worker.start()
    worker.ready.wait()
    return worker


class CeleryTestCase(CeleryTestCaseMixin, SimpleTestCase):
    """
    Extends SimpleTest case instead of
    TestCase which extends TransactionTestCase.
    This way celery can see database changes
    because test are not wrapped into transaction.
    Stack Overflow post about the problem
    https://stackoverflow.com/a/46564964/1580061

    """
    allow_database_queries = True
    celery_app = example_celery_app
    celery_concurrency = 4

    delay = .1
    overhead_time = 0.05

    @classmethod
    def setUpClass(cls):
        super(CeleryTestCase, cls).setUpClass()
        cls.username1 = 'user1'
        cls.password1 = 'password1'
        try:
            cls.user1 = User.objects.get(username=cls.username1)
        except User.DoesNotExist:
            cls.user1 = User.objects.create_user(
                username=cls.username1, password=cls.password1)

        cls.username2 = 'user2'
        cls.password2 = 'password2'
        try:
            cls.user2 = User.objects.get(username=cls.username2)
        except User.DoesNotExist:
            cls.user2 = User.objects.create_user(
                username=cls.username2, password=cls.password2)

    def assert_tempfile_count_change(
            self, original_tempfile_count, expected_change, extra_message=''):
        cur_tempfile_count = TempFile.objects.count()
        tempfile_count_change = cur_tempfile_count - original_tempfile_count
        self.assertEqual(
            expected_change, tempfile_count_change,
            'Expected {} new TempFile in database. {}got {}'
            .format(expected_change, extra_message, tempfile_count_change)
        )

    def assert_temp_files(self, user, original_tempfile_count,
                          original_tempfile_ids, expected_to_be_deleted_count):
        self.assert_tempfile_count_change(
            original_tempfile_count, 1 - expected_to_be_deleted_count)
        new_tempfiles = TempFile.objects.all().exclude(id__in=original_tempfile_ids)
        self.assertEqual(len(new_tempfiles), 1)
        new_tempfile = new_tempfiles[0]
        self.assertEqual(new_tempfile.user, user)
        self.assertEqual(new_tempfile.description, self.expected_tempfile_description)

    def assertIsJSON(self, raw):
        try:
            data = json.loads(raw.decode('utf-8'))
        except ValueError:
            self.fail("First argument is not valid JSON: %r" % raw)
        return data

    @classmethod
    def start_worker(cls):
        return _start_celery_worker(cls.celery_app)


class CeleryTestCaseNoDBMixin(object):
    def assert_tempfile_count_change(
            self, original_tempfile_count, expected_change, extra_message=''):
        extra_message = 'ASYNC_VIEW_AND_DOWNLOAD_USE_DB=False '
        expected_change = 0
        super(CeleryTestCaseNoDBMixin, self).assert_tempfile_count_change(
            original_tempfile_count, expected_change, extra_message
        )

    def assert_temp_files(self, user, original_tempfile_count,
                          original_tempfile_ids, expected_to_be_deleted_count):
        pass
