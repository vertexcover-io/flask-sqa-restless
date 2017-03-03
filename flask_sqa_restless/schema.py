# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import functools

from builtins import super
from marshmallow import fields

from marshmallow_sqlalchemy import ModelConverter, ModelSchemaOpts, ModelSchema
from marshmallow_sqlalchemy.convert import _has_default, validate
from restless.utils import MoreTypesJSONEncoder
from sqlalchemy.dialects import postgresql


def array_field_converter(converter, data_type):
    assert isinstance(data_type, postgresql.ARRAY)

    return functools.partial(
        fields.List,
        converter.get_field_for_data_type(data_type.item_type)
    )


class BaseModelConverter(ModelConverter):
    @classmethod
    def update_sqla_type_mapper(cls, mapping):
        """
        Updates the dictionary mapping sqlalchemy fields to marshmallow field types
        :param dict mapping: Mapping from sqlalchemy field type to marshmallow field type
        """
        cls.SQLA_TYPE_MAPPING.update(mapping)

    def _add_column_kwargs(self, kwargs, column):
        """Add keyword arguments to kwargs (in-place) based on the passed in
        `Column <sqlalchemy.schema.Column>`.
        """

        super(BaseModelConverter, self)._add_column_kwargs(kwargs, column)
        self._add_data_type_kwargs(kwargs, column.type)

    def _add_data_type_kwargs(self, kwargs, data_type):
        pass

    def get_field_for_data_type(self, data_type, **kwargs):
        field_class = self._get_field_class_for_data_type(data_type)
        field_kwargs = self.get_base_kwargs()
        self._add_data_type_kwargs(field_kwargs, data_type)
        field_kwargs.update(field_kwargs)
        return field_class(**field_kwargs)


BaseModelConverter.update_sqla_type_mapper({
    postgresql.ARRAY: array_field_converter
})


class BaseModelSchemaOpts(ModelSchemaOpts):
    """
    Options class for `BaseModelSchema`. Overrides the default model converter and
    simplifies extension by simply specifying overriding following class variables -

    - ``DEFAULT_MODEL_CONVERTER``: `ModelConverter` class to use for converting the SQLAlchemy model to
        marshmallow fields; defaults to `BaseModelConverter`
    - ``DEFAULT_SQLA_SESSION``: SQLAlchemy session to be used for deserialization
    - ``INCLUDE_FK``: Whether to include foreign fields; defaults to `False`.
    - ``DEFUALT_JSON_ENCODER``: JSON Encoder to user while serializing

    """
    DEFAULT_MODEL_CONVERTER = BaseModelConverter

    DEFAULT_SQLA_SESSION = None

    DEFAULT_JSON_ENCODER = MoreTypesJSONEncoder

    INCLUDE_FK = False

    def __init__(self, meta):
        meta.sqla_session = getattr(meta, 'sqla_session',
                                    self.DEFAULT_SQLA_SESSION)
        meta.model_converter = getattr(meta, 'model_converter',
                                       self.DEFAULT_MODEL_CONVERTER)
        meta.include_fk = getattr(meta, 'include_fk', self.INCLUDE_FK)
        ModelSchemaOpts.__init__(self, meta)
        self.json_encoder = getattr(meta, 'json_encoder',
                                    self.DEFAULT_JSON_ENCODER)


class BaseModelSchema(ModelSchema):
    """
    Base class for SQLAlchemy model-based Schema used by REST API Resource
    """
    OPTIONS_CLASS = BaseModelSchemaOpts

    def __init__(self, *args, **kwargs):
        kwargs['only'] = ()
        kwargs['exclude'] = ()
        ModelSchema.__init__(self, *args, **kwargs)

    def dumps(self, obj, many=None, update_fields=True, *args, **kwargs):
        kwargs['cls'] = self.opts.json_encoder
        return ModelSchema.dumps(obj, many, update_fields, *args, **kwargs)

    def include_fields_serialize(self, include_fields):
        """
        Set a list/tuple of fields to serialize. If include_fields is `[*]`,
        then all fields are serialized
        :param tuple include_fields: List of fields to serialize or `[*]` to
        serialize all fields
        """
        if include_fields == ['*']:
            self.load_only = set()
        else:
            all_fields = set(self.declared_fields.keys())
            include_fields = set(include_fields)
            self.load_only = all_fields - include_fields

        self._update_fields()

    def include_fields_deserialize(self, include_fields):
        """
        Set a list/tuple of fields to deserialize. If include_fields is `[*]`,
        then all fields are deserialized
        :param tuple include_fields: List of fields to deserialize or `[*]` to
        deserialize all fields
        """

        if include_fields == ['*']:
            self.dump_only = set()
        else:
            all_fields = set(self.declared_fields.keys())
            include_fields = set(include_fields)
            self.dump_only = all_fields - include_fields

        self._update_fields()

    def exclude_fields_deserialize(self, exclude_fields=()):
        """
        Set a list/tuple of fields to exclude while serializing. If exclude_fields is None,
        then no fields are excluded
        :param tuple exclude_fields: List of fields to exclude while serializing or None to
        serialize all fields
        """

        self.dump_only = set(exclude_fields)
        self._update_fields()

    def exclude_fields_serialize(self, exclude_fields):
        """
        Set a list/tuple of fields to exclude while deserializing. If exclude_fields is None,
        then no fields are excluded
        :param tuple exclude_fields: List of fields to exclude while deserializing or None to
        deserialize all fields
        """

        self.load_only = set(exclude_fields)
        self._update_fields()
