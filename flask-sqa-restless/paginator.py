# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from urllib.parse import urlencode
import six
from werkzeug.exceptions import BadRequest


class SQLAlchemyPaginator(object):
    """
    Limits result sets down to sane amounts for passing to the client.
    This implementation also provides additional details like the
    ``total_count`` of resources seen and convenience links to the
    ``previous``/``next`` pages of data as available.
    """

    MAX_LIMIT = 100

    def __init__(self, request_data, query=None, resource_uri=None,
                 max_limit=None):
        """

        :param dict request_data: A dictionary like object that might provide
        ``limit`` and/or ``offset`` to override the defaults. Commonly provide by
         ``request.args`` (required)
        :param query: SqlAlchemy ``Query`` object (required)
        :param resource_uri: uri for the resource. Used to construct next and previous uri
        :param int max_limit: An upper bound to limit. Defaults to ``MAX_LIMIT``
        :return:
        """
        self.request_data = request_data
        self.query = query
        self.resource_uri = resource_uri
        self.max_limit = [max_limit or self.MAX_LIMIT]

    def get_limit(self):
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
            return self.max_limit

        return limit

    def get_offset(self):
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

    def get_sliced_query(self, limit, offset):
        """
        Slices the result set to the specified ``limit`` & ``offset``.
        """
        if limit == 0:
            return self.query.offset(offset)

        return self.query.offset(offset).limit(limit)

    def get_previous(self, limit, offset):
        """
        If a previous page is available, will generate a URL to request that
        page. If not available, this returns ``None``.
        """
        if offset - limit < 0:
            return None

        return self._generate_uri(limit, offset - limit)

    def get_next(self, limit, offset, count=None):
        """
        If a next page is available, will generate a URL to request that
        page. If not available, this returns ``None``.
        """

        if count and offset + limit >= count:
            return None

        return self._generate_uri(limit, offset+limit)

    def _generate_uri(self, limit, offset):
        if self.resource_uri is None:
            return None

        request_params = {}

        for k, v in self.request_data.items():
            if isinstance(v, six.text_type):
                request_params[k] = v.encode('utf-8')
            else:
                request_params[k] = v

        request_params.update({'limit': limit, 'offset': offset})
        encoded_params = urlencode(request_params, doseq=True)

        return '%s?%s' % (self.resource_uri, encoded_params)

    def get_meta(self, object_count):
        limit = self.get_limit()
        offset = self.get_offset()
        meta = {
            'offset': offset,
            'limit': limit,
            'count': object_count
        }

        if limit:
            meta['previous'] = self.get_previous(limit, offset)
            meta['next'] = self.get_next(limit, offset) \
                if object_count >= limit else None

        return meta

    def page(self):
        """
        Generates all pertinent data about the requested page.
        Handles getting the correct ``limit`` & ``offset``, then slices off
        the correct set of results and returns all pertinent metadata.
        """
        if not self.query:
            raise ValueError('Query object cannot be empty')

        limit = self.get_limit()
        offset = self.get_offset()
        query = self.get_sliced_query(limit, offset)
        return query