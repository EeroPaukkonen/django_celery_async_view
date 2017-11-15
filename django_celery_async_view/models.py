# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone

DEFAULT_TEMP_FILE_DURATION_MS = 10 * 60 * 1000  # 10min


class TempFileManager(models.Manager):

    def delete_old_files(self):
        """
        Deletes this files that are older than TempFile.duration.
        :return:
        """
        self.filter(
            created_datetime__lte=
            timezone.now() - F('duration')
        ).delete()


class TempFile(models.Model):
    bytes = models.TextField()
    filename = models.CharField(max_length=1000)
    mimetype = models.CharField(max_length=255)

    # auto_now_add set only when model is created
    created_datetime = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(
        default=timedelta(
            milliseconds=getattr(
                settings, 'ASYNC_VIEW_TEMP_FILE_DURATION_MS',
                DEFAULT_TEMP_FILE_DURATION_MS)))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True
    )

    description = models.TextField(default='', blank=True, null=False)

    objects = TempFileManager()
