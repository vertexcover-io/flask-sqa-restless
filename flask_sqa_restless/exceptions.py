# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
import re
from werkzeug.exceptions import BadRequest, Conflict

from . import util


def get_formatted_error(error_dict, message, exception_type):

    msg = "%s: " % message if message else ''

    for field, err in error_dict.items():
        msg += '{}: {} '.format(util.capitalize_underscore_string(field), err)

    return exception_type(description=msg)


def get_validation_error(error_dict, message=None):
    message = message or 'Validation Error'
    return get_formatted_error(error_dict, message, exception_type=ValidationError)


def get_conflict_error(error_dict, message=None):
    message = message or 'Conflict'
    return get_formatted_error(error_dict, message, exception_type=Conflict)


class InvalidFilterError(BadRequest):
    """
    Raised when the end user attempts to use a filter that has not be
    explicitly allowed.
    """
    pass


class ValidationError(BadRequest):
    """
    Raised when validation error occurs while deserializing mdodel resource
    """
    pass


class HttpErrorConvertible(object):
    def get_http_error(self):
        return Exception(self.message)

    def raise_http_error(self):
        raise self.get_http_error()


class DatabaseError(Exception, HttpErrorConvertible):

    def __init__(self, integrity_error):
        self.error = integrity_error
        self.message = self.format_error()
        self.error_code = self.error.orig.pgcode
        super(DatabaseError, self).__init__(self.format_error())

    def __repr__(self):
        return self.message

    def format_error(self):
        return self.error.orig.diag.message_primary

    def get_http_error(self):
        return BadRequest(self.message)

    def error_type(self):
        return self.__class__.__name__


class BaseConstraintError(DatabaseError):

    RE_ERROR_MESSAGE = re.compile(r'\(([^)]+)\)=\(([^)]*)\)')

    @classmethod
    def parse_column(cls, error):
        match = cls.RE_ERROR_MESSAGE.search(error.message_detail)
        if match:
            return match.groups()
        else:
            return error.column_name, None


class UniqueConstraintError(BaseConstraintError):

    MESSAGE_FORMAT = "A record with this field(s) {0} " \
                     "already exists"

    def __init__(self, integrity_error):
        self.column, self.value = self.parse_column(integrity_error.orig.diag)
        super(UniqueConstraintError, self).__init__(integrity_error)

    def format_error(self):
        if self.column and self.value:
            arg = "%s('%s')" % (self.column, self.value)
            return self.MESSAGE_FORMAT.format(arg)
        elif self.column:
            return self.MESSAGE_FORMAT.format(self.column)

        else:
            return 'Duplicate Record Error'

    def get_http_error(self):
        error_dict = {self.column: self.message}
        return get_conflict_error(error_dict)


class NotNullError(DatabaseError):

    MESSAGE_FORMAT = "'{}' field cannot be empty"

    def __init__(self, integrity_error):
        self.column = integrity_error.orig.diag.column_name
        super(NotNullError, self).__init__(integrity_error)

    def format_error(self):
        return self.MESSAGE_FORMAT.format(self.column)

    def get_http_error(self):
        error_dict = {self.column: self.message}
        get_validation_error(error_dict)


class ForeignKeyConstraintError(BaseConstraintError):

    MESSAGE_FORMAT = "Foreign Key Error: {}"

    def __init__(self, integrity_error):
        self.column, self.value = self.parse_column(integrity_error.orig.diag)
        super(ForeignKeyConstraintError, self).__init__(integrity_error)

    def format_error(self):
        return self.MESSAGE_FORMAT.format(self.error.orig.diag.message_detail)

    def get_http_error(self):
        error_dict = {self.column: self.message}
        return get_conflict_error(error_dict)


POSTGRESS_ERROR_MAP = {
    '23505': UniqueConstraintError,
    '23502': NotNullError,
    '23503': ForeignKeyConstraintError
}


def get_database_error(integrity_error):
    error_code = integrity_error.orig.pgcode
    if error_code in POSTGRESS_ERROR_MAP:
        error_cls = POSTGRESS_ERROR_MAP[error_code]
        return error_cls(integrity_error)
    else:
        return DatabaseError(integrity_error)
