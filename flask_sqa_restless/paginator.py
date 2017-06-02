# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from six.moves.urllib.parse import urlencode
import six
from cached_property import cached_property
from .exceptions import BadRequest


class SQLAlchemyPaginator(object):
    """
    Limits result sets down to sane amounts for passing to the client.
    This implementation also provides additional details like the
    ``total_count`` of resources seen and convenience links to the
    ``previous``/``next`` pages of data as available.
    """

    MAX_LIMIT = 100

    def __init__(self, request_data, resource_uri=None,
                 max_limit=None):
        """

        :param dict request_data: A dictionary like object that might provide
        ``limit`` and/or ``offset`` to override the defaults. Commonly provide by
         ``request.args`` (required)
        :param resource_uri: uri for the resource. Used to construct next and previous uri
        :param int max_limit: An upper bound to limit. Defaults to ``MAX_LIMIT``
        :return:
        """
        self.request_data = request_data
        self.resource_uri = resource_uri
        self.query = None
        self.max_limit = [max_limit or self.MAX_LIMIT]

    @cached_property
    def limit(self):
        # request_data.get('limit') -> returns a list
        limit = self.request_data.get('limit', self.max_limit)[0]

        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest("Invalid limit '%s' provided. "
                             "Please provide a positive integer." % limit)

        if limit < 0:
            raise BadRequest("Invalid limit '%s' provided. Please provide a"
                             " positive integer >= 0." % limit)

        if self.max_limit and (not limit or limit > self.max_limit):
            # If it's more than the max, we're only going to return the max.
            # This is to prevent excessive DB (or other) load.
            limit = self.max_limit

        return limit

    @cached_property
    def offset(self):
        """
        Determines the proper starting offset of results to return.
        It attempts to use the user-provided ``offset`` from the GET parameters,
        if specified. Otherwise, it falls back to the object-level ``offset``.
        Default is 0.
        """
        offset = self.request_data.get('offset', [0])[0]

        try:
            offset = int(offset)
        except ValueError:
            raise BadRequest("Invalid offset '%s' provided. "
                             "Please provide an integer." % offset)

        if offset < 0:
            raise BadRequest("Invalid offset '%s' provided. Please provide "
                             "a positive integer >= 0." % offset)

        return offset

    @cached_property
    def count(self):
        if self.query:
            return self.query.count()
        else:
            return 0

    def get_sliced_query(self):
        """
        Slices the result set to the specified ``limit`` & ``offset``.
        """
        query = self.query
        if self.offset:
            query = query.offset(self.offset)

        if self.limit:
            return query.limit(self.limit)

    def get_previous(self):
        """
        If a previous page is available, will generate a URL to request that
        page. If not available, this returns ``None``.
        """
        if self.offset - self.limit < 0:
            return None

        return self._generate_uri()

    def get_next(self):
        """
        If a next page is available, will generate a URL to request that
        page. If not available, this returns ``None``.
        """

        if self.count and self.offset + self.limit >= self.count:
            return None

        return self._generate_uri()

    def _generate_uri(self):
        if self.resource_uri is None:
            return None

        request_params = {}

        for k, v in self.request_data.items():
            if isinstance(v, six.text_type):
                request_params[k] = v.encode('utf-8')
            else:
                request_params[k] = v

        request_params.update({'limit': self.limit, 'offset': self.offset})
        encoded_params = urlencode(request_params, doseq=True)

        return '%s?%s' % (self.resource_uri, encoded_params)

    def get_meta(self):
        meta = {
            'offset': self.offset,
            'limit': self.limit,
            'count': self.count
        }

        return meta

    def _set_query(self, query):
        self.query = query
        if 'count' in self.__dict__:
            del self.__dict__['count']

        # memoize count
        count = self.count

    def page(self, query):
        """
        Generates all pertinent data about the requested page.
        Handles getting the correct ``limit`` & ``offset``, then slices off
        the correct set of results and returns all pertinent metadata.
        """
        if not query:
            raise ValueError('Query object cannot be empty')

        self._set_query(query)
        query = self.get_sliced_query()
        return query