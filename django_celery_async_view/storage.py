# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import base64

import six
from db_file_storage.storage import FixedModelDatabaseFileStorage


class TempFileDatabaseFileStorage(FixedModelDatabaseFileStorage):

    def __init__(self, require_unique_filenames=False, *args, **kwargs):
        self.require_unique_filenames = require_unique_filenames
        super(TempFileDatabaseFileStorage, self).__init__(*args, **kwargs)

    def _get_encoded_bytes_from_file(self, _file):
        if isinstance(_file, six.string_types):
            file_content = _file
        else:
            _file.seek(0)
            file_content = _file.read()
        return base64.b64encode(file_content)

    def _save(self, name, content, user_id=None, mimetype=None, **create_kwargs):
        """
        Overrides to allow
            - support for user_id
            - return new_model_object instead of new_filename
            - require_unique_filenames = False support
        :param name:
        :param content:
        :return:
        """
        storage_attrs = self._get_storage_attributes(name)
        model_class_path = storage_attrs['model_class_path']
        content_field = storage_attrs['content_field']
        filename_field = storage_attrs['filename_field']
        mimetype_field = storage_attrs['mimetype_field']

        model_cls = self._get_model_cls(model_class_path)
        if self.require_unique_filenames:
            new_filename = self._get_unique_filename(
                model_cls, filename_field, name)
        else:
            new_filename = name
        encoded_bytes = self._get_encoded_bytes_from_file(content)
        if mimetype is None:
            mimetype = getattr(content.file, 'content_type', 'text/plain')

        create_kwargs.update({
            content_field: encoded_bytes,
            filename_field: new_filename,
            mimetype_field: mimetype,
        })
        if user_id is not None:
            create_kwargs['user_id'] = user_id

        new_model_object = model_cls.objects.create(**create_kwargs)
        # return new_filename
        return new_model_object
