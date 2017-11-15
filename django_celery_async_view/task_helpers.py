# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64
from copy import deepcopy
from datetime import timedelta

from django.conf import settings

from django_celery_async_view.models import TempFile, DEFAULT_TEMP_FILE_DURATION_MS
from django_celery_async_view.storage import TempFileDatabaseFileStorage


def create_storage():
    return TempFileDatabaseFileStorage(
        model_class_path='django_celery_async_view.TempFile',
        content_field='bytes',
        filename_field='filename',
        mimetype_field='mimetype',
    )


def open_result(result):
    """

    :param result:
    :return: opened_result = {
            'content': <decoded file content>,
            'user_id': <user_id>,
            'filename': <filename>,
            'mimetype': <mimetype>,
        }
    """
    if result is None:
        return None
    if type(result) is dict:
        opened_result = deepcopy(result)
    else:
        temp_file = TempFile.objects.get(id=result)
        opened_result = {
            'content': temp_file.bytes,
            'user_id': temp_file.user_id,
            'filename': temp_file.filename,
            'mimetype': temp_file.mimetype,
        }
    opened_result['content'] = base64.b64decode(opened_result['content'])
    return opened_result


class AbstractAsyncDownloadCreateFile(object):
    description = ''
    use_db = True

    def __init__(self, description=None, use_db=None):
        if description is not None:
            self.description = description
        if use_db is not None:
            self.use_db = use_db

    def create_file(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return: _file, filename, mimetype
        """
        raise NotImplementedError('This must be implemented when extending.')

    def run_use_result_backend(self, user_id,
                               *create_file_args,
                               **create_file_kwargs):
        _file, filename, mimetype = self.create_file(
            *create_file_args,
            **create_file_kwargs
        )
        encoded_file = create_storage()._get_encoded_bytes_from_file(_file)
        return {
            'content': encoded_file,
            'user_id': user_id,
            'filename': filename,
            'mimetype': mimetype,
        }

    def run_use_db(self, user_id,
                   *create_file_args,
                   **create_file_kwargs):
        """
        # 1) Delete all too old files
        # 2) Create file
        # 3) Save file to database
        :param user_id:
        :param create_file_args:
        :param create_file_kwargs:
        :return:
        """
        # 1) Delete all too old files
        TempFile.objects.delete_old_files()
        # 2) Create file
        _file, filename, mimetype = self.create_file(
            *create_file_args,
            **create_file_kwargs
        )
        # 3) Save file to database
        storage = create_storage()
        new_temp_file = storage._save(
            name=filename, content=_file,
            user_id=user_id, mimetype=mimetype,
            description=self.description,
            duration=self.get_tempfile_duration()
        )
        return new_temp_file.id

    def run(self, user_id,
            *create_file_args,
            **create_file_kwargs):
        if self.use_db:
            return self.run_use_db(
                user_id,
                *create_file_args,
                **create_file_kwargs)
        else:
            return self.run_use_result_backend(
                user_id,
                *create_file_args,
                **create_file_kwargs)

    def get_tempfile_duration(self):
        return timedelta(getattr(
            settings, 'ASYNC_VIEW_TEMP_FILE_DURATION_MS', DEFAULT_TEMP_FILE_DURATION_MS))


class AsyncViewReturnHTML(AbstractAsyncDownloadCreateFile):

    def create_file(self, html_string, *args, **kwargs):
        # filename and mimetype are not used
        # file_content, filename, mimetype
        return html_string, 'async-view.html', 'text/html'

    def run(self, user_id, html_string):
        return super(AsyncViewReturnHTML, self).run(
            user_id=user_id,
            html_string=html_string)
