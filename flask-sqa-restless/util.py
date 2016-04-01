# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
import operator
from six import wraps

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import class_mapper

from .exceptions import *


def multi_getter(obj, *args):
    return operator.attrgetter(*args)(obj)


def capitalize_underscore_string(string):
    list_words = [word[0].upper() + word[1:] for word in string.split('_')]
    return " ".join(list_words)


def get_mapper_cls_fields(cls):
    return [prop.key for prop in class_mapper(cls).iterate_properties
            if isinstance(prop, sa.orm.ColumnProperty)]


def db_http_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as ex:
            db_error = get_database_error(ex)
            db_error.raise_http_error()

        except HttpErrorConvertible as ex:
            ex.raise_http_error()

    return wrapper


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
