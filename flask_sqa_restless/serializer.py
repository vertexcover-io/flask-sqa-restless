# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division

from copy import deepcopy

from marshmallow import fields
from restless.serializers import JSONSerializer

from restless.utils import json, MoreTypesJSONEncoder

from .schema import BaseModelSchema
from .exceptions import ValidationError


class SimpleJSONSerializer(JSONSerializer):

    def __init__(self, json_encoder=MoreTypesJSONEncoder):
        self._json_encoder = json_encoder

    def serialize(self, data):
        return json.dumps(data, cls=self._json_encoder)

    def serialize_model(self, data):
        return self.serialize(data)

    def deserialize_model(self, obj_dict):
        return obj_dict


class ModelJSONSerializer(BaseModelSchema, SimpleJSONSerializer):

    def __init__(self, *args, **kwargs):
        BaseModelSchema.__init__(self, *args, **kwargs)
        SimpleJSONSerializer.__init__(self, self.opts.json_encoder)

    @property
    def model(self):
        return self.opts.model

    def serialize_model(self, data):
        if isinstance(data, self.model):
            resp = self.dump(data).data

        elif isinstance(data, dict):
            resp = {}
            for key, value in data.iteritems():
                resp[key] = self.serialize_model(value)

        elif isinstance(data, (list, tuple)):
            if data and isinstance(data[0], self.model):
                resp = self.dump(data, many=True).data
            else:
                resp = data
        else:
            resp = data

        return resp

    def deserialize_model(self, obj_dict, **kwargs):
        if kwargs.get('partial'):
            self._nest_partial_fields()

        data, errors = BaseModelSchema.load(self, obj_dict, **kwargs)
        if errors:
            raise ValidationError(payload=self._parse_validation_error(errors))

        return data

    def _nest_partial_fields(self):
        for field_name, field in self.fields.items():
            if isinstance(field, fields.Nested):
                new_field = deepcopy(field)
                new_field.schema.partial = True
                self.fields[field_name] = new_field

    def _parse_validation_error(self, errors, field_prefix=None):
        errors_dict = {}
        for field, error in errors.items():
            field = "{}.{}".format(field_prefix, field) if field_prefix else field
            if isinstance(error, (tuple, list)):
                errors_dict[field] = ", ".join(error)
            elif isinstance(error, dict):
                errors_dict[field] = self._parse_validation_error(error)
            else:
                errors_dict[field] = error

        return errors_dict

    @property
    def content_type(self):
        return 'application/json'
