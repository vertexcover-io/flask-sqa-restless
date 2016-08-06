# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
import re

from . import util


class HTTPException(Exception):
    code = None
    description = None

    def __init__(self, description=None, payload=None, code=None):
        if description is not None:
            self.description = description

        Exception.__init__(self, description)

        if code is not None:
            self.code = code

        self.payload = payload


class BadRequest(HTTPException):
    code = 400
    description = 'Bad Request'


class SecurityError(BadRequest):

    """Raised if something triggers a security error.  This is otherwise
    exactly like a bad request error.
    """


class UnAuthorized(HTTPException):
    code = 401
    description = 'Authentication Failed'


class PermissionDenied(HTTPException):
    code = 403
    description = 'Permission Denied'


class NotFound(HTTPException):
    code = 404
    description = 'The request Resource is not found'


class MethodNotAllowed(HTTPException):
    code = 405
    description = 'The method is not allowed for the requested URL.'


class RequestTimeout(HTTPException):
    code = 408
    description = 'Request Timeout'


class HTTPConflict(HTTPException):
    code = 409
    description = (
        'A conflict happened while processing the request. The resource might '
        'have been modified while the request was being processed.'
    )


class Gone(HTTPException):
    code = 410
    description = 'Request URL is no longer available'


class ServerError(HTTPException):
    code = 500
    description = 'Server Error. Something went wrong'


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
    description = 'Validation Error'


class MethodNotImplemented(HTTPException):
    code = 501
    description = "The specified HTTP method is not implemented."


class HttpErrorConvertible(object):
    code = 500
    description = "Something Went Wrong"

    def get_http_error(self):
        return HTTPException(description=self.description, code=self.code)

    def raise_http_error(self):
        raise self.get_http_error()

    def __repr__(self):
        return self.description


class DatabaseError(Exception, HttpErrorConvertible):

    def __init__(self, integrity_error):
        self.error = integrity_error
        self.description = self.format_error()
        self.error_code = self.error.orig.pgcode
        super(DatabaseError, self).__init__(self.description)

    def format_error(self):
        return self.error.orig.diag.message_primary

    def get_http_error(self):
        return BadRequest(self.description)

    def error_type(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.description


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

    MESSAGE_FORMAT = "A record with this {0} already exists"

    def __init__(self, integrity_error):
        self.column, self.value = self.parse_column(integrity_error.orig.diag)
        super(UniqueConstraintError, self).__init__(integrity_error)

    def format_error(self):
        if self.column:
            return self.MESSAGE_FORMAT.format(self.column)

        else:
            return 'Duplicate Record Error'

    def get_http_error(self):
        error_dict = {self.column: self.message}
        return HTTPConflict(description=self.description,
                            payload=error_dict)


class NotNullError(DatabaseError):

    MESSAGE_FORMAT = "'{}' field cannot be empty"

    def __init__(self, integrity_error):
        self.column = integrity_error.orig.diag.column_name
        super(NotNullError, self).__init__(integrity_error)

    def format_error(self):
        return self.MESSAGE_FORMAT.format(self.column)

    def get_http_error(self):
        error_dict = {self.column: self.description}
        return ValidationError(description=self.description,
                               payload=error_dict)


class ForeignKeyConstraintError(BaseConstraintError):

    MESSAGE_FORMAT = "Foreign Key Error: {}"

    def __init__(self, integrity_error):
        self.column, self.value = self.parse_column(integrity_error.orig.diag)
        super(ForeignKeyConstraintError, self).__init__(integrity_error)

    def format_error(self):
        return self.MESSAGE_FORMAT.format(self.error.orig.diag.message_detail)

    def get_http_error(self):
        error_dict = {self.column: self.description}
        return BadRequest(description=self.description,
                          payload=error_dict)


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
