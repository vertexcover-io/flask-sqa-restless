# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division


class ToJSONMixin(object):

    def __init__(self):
        assert hasattr(self, '__serializer__'), \
            'The actual class inheriting this mixin must have a serializer defined'

    def get_serializer(self):
        serializer_cls = getattr(self, '__serializer__')
        return serializer_cls()

    def to_dict(self, include_fields=None,
                exclude_fields=None):

        serializer = self.get_serializer()
        return serializer.serialize_model(include_fields, exclude_fields)

    def to_json(self, include_fields=None,
                exclude_fields=None):
        serializer = self.get_serializer()
        return serializer.serialize(include_fields, exclude_fields)
