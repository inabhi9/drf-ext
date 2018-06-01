"""
======
Errors
======
This module holds exceptions for all other app
"""
from django.utils.translation import ugettext as _

from rest_framework import exceptions


class Messages(object):
    """
    Helper class to hold error message and its for each app

    Error code is consist of 2 digit prefix which indicates the app and the 2 digits error code
    """

    #: System wide unexpected error
    UNEXPECTED = _('Unexpected error occurred'), -1


class APIException(exceptions.APIException):
    """
    Exception class that caught by renderer and produce pretty output.

    It also has ``error_code`` attribute that may be set by other app otherwise it'll be ``-1``
    """

    def __init__(self, detail=None, error_code=-1, param=None):
        if isinstance(param, dict):
            detail = detail.format(**param)
        super(APIException, self).__init__(detail=detail)
        self.error_code = error_code
