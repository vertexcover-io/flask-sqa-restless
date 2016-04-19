# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from . import util


class Authentication(object):
    """
    A simple base class to establish the protocol for auth.
    By default, this indicates the user is always authenticated.
    """

    def is_authenticated(self, method, endpoint, **kwargs):
        """
        Identifies if the user is authenticated to continue or not.
        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        return True


class MultiAuthentication(Authentication):

    def __init__(self, *backends, **kwargs):
        self.auth_backends = backends
        self.match_all = kwargs.get("match_all", False)

        if not self.auth_backends:
            raise ValueError("Atleast one backend must be provided")

    def is_authenticated(self, *args, **kwargs):
        for backend in self.auth_backends:
            resp = backend.is_authenticated(*args, **kwargs)
            if self.match_all:
                if not resp:
                    return False

            else:
                if resp:
                    return True

        return self.match_all


class Authorization(object):

    ANY = 'ANY'
    OBJECT_FILTER = 'OBJECT_FILTER'
    DATA_FILTER = 'DATA_FILTER'

    def __init__(self, allowed_roles=None, object_perm_filter=None):
        self.allowed_roles = allowed_roles or {}
        self.object_perm_filter = object_perm_filter

    def is_authorized(self, user, view, data, *args, **kwargs):
        roles = self.allowed_roles.get(view, self.allowed_roles.get('default'))
        if not roles:
            return False

        if self.ANY in roles or user.user_type in roles:
            return True

        elif self.OBJECT_FILTER in roles and self.object_perm_filter:
            if self.DATA_FILTER in roles and not self.check_data_filter(data, user):
                return False
            try:
                return self.get_perm_filter(user)
            except AttributeError:
                return False

        elif self.DATA_FILTER in roles and self.object_perm_filter:
            return self.check_data_filter(data, user)
        else:
            return False

    def check_data_filter(self, data, user):
        field = self.object_perm_filter[0]
        try:
            value = util.multi_getter(user, self.object_perm_filter[1])
        except AttributeError:
            return False

        if isinstance(data, list):
            for item in data:
                if field in item and item[field] != value:
                    return False
        elif field in data and data[field] != value:
            return False

        return True

    def get_perm_filter(self, user):
        return {self.object_perm_filter[0]: util.multi_getter(user, self.object_perm_filter[1])}


