# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division

import importlib
import operator
import inspect

import six
import sqlalchemy as sa
from sqlalchemy.inspection import inspect as sqa_inspect

from sqlalchemy.orm import class_mapper


def multi_getter(obj, *args):
    return operator.attrgetter(*args)(obj)


def capitalize_underscore_string(string):
    list_words = [word[0].upper() + word[1:] for word in string.split('_')]
    return " ".join(list_words)


def get_mapper_cls_fields(cls):
    return [prop.key for prop in class_mapper(cls).iterate_properties
            if isinstance(prop, sa.orm.ColumnProperty)]


def convert_value_to_python(value):
    """
    Turn the string ``value`` into a python object.
    """
    # Simple values
    if value in ['true', 'True', True]:
        value = True
    elif value in ['false', 'False', False]:
        value = False
    elif value in ('nil', 'none', 'None', None):
        value = None

    return value


def get_primary_keys(cls_or_instance):
    cls = cls_or_instance.__class__ if not inspect.isclass(cls_or_instance) \
        else cls_or_instance
    return [key.name for key in sa.inspect(cls).primary_key]


def get_model_relationship_names(model):
    return sqa_inspect(model).relationships.keys()


def import_class(cls_path):
    if not isinstance(cls_path, six.string_types):
        return cls_path

    # cls is a module path to string
    if '.' in cls_path:
        # Try to import.
        module_bits = cls_path.split('.')
        module_path, class_name = '.'.join(module_bits[:-1]), module_bits[-1]
        module = importlib.import_module(module_path)
    else:
        # We've got a bare class name here, which won't work (No AppCache
        # to rely on). Try to throw a useful error.
        raise ImportError("Requires a Python-style path (<module.module.Class>) "
                          "to load given cls. Only given '%s'." % cls_path)

    cls = getattr(module, class_name, None)

    if cls is None:
        raise ImportError(
            "Module '{}' does not appear to have a class called '{}'.".format(
                module_path, class_name))

    return cls
