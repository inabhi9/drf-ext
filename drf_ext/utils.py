"""
=======
Helpers
=======
Useful helper methods that frequently used in this project
"""
import collections

import datetime
import inspect
import logging
import ntpath
import re
import sys
import traceback
from contextlib import contextmanager

import pytz
from django.conf import settings
from django.core.cache import cache
from rest_framework.views import exception_handler

from . import errors as err

L = logging.getLogger('app.' + __name__)

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def custom_exception_handler(exc, context):
    """
    Replace rest_framework's default handler to generate error response as per API specification
    """

    #: Call REST framework's default exception handler first,
    #: to get the standard error response.
    response = exception_handler(exc, context)
    request = context.get('request')

    # Getting originating location of exception
    frm = inspect.trace()[-1]
    mod = inspect.getmodule(frm[0])
    func = traceback.extract_tb(sys.exc_info()[2])[-1][2]
    log_extra = {'request': request, 'request_id': request.id,
                 'culprit': "%s in %s" % (mod.__name__, func)}

    if response is None and settings.DEBUG:
        return response

    if response:
        L.warning(exc, extra=log_extra, exc_info=True)
    else:
        L.exception(exc, extra=log_extra)

    # Response is none, meaning builtin error handler failed to generate response and it needs to
    #  be converted to json response
    if response is None:
        return custom_exception_handler(err.APIException(*err.m.UNEXPECTED), context)

    # Passing context to help the renderer to identify if response is error or normal data
    if isinstance(response.data, list):
        response.data = response.data[0]

    response.data['_context'] = 'error'
    response.data['type'] = exc.__class__.__name__
    response.data['status_code'] = response.status_code
    response.data['error_code'] = getattr(exc, 'error_code', 0)

    return response


def str2bool(v):
    """
    Converts string to bool. True for any term from "yes", "true", "t", "1"

    :param str v: Term
    :return bool:
    """
    try:
        return v.lower() in ("yes", "true", "t", "1")
    except:
        return False


def prop2pair(cls, out='tuple', startswith_only=None):
    """
    Iterates over each property of the cls and prepare the key-value pair

    :param cls: Class to be interated over
    :param str out: Output format either `tuple` or `dict`
    :param str startswith_only: Consider only properties that starts with this value
    :return tuple,dict:
    """
    if startswith_only is not None:
        d = {
            getattr(cls, prop)[0]:
                getattr(cls, prop)[1] if getattr(cls, prop)[1] else getattr(cls, prop)[0]
            for prop in dir(cls) if prop.startswith(startswith_only) is True
        }
    else:
        d = {
            getattr(cls, prop)[0]:
                getattr(cls, prop)[1] if getattr(cls, prop)[1] else getattr(cls, prop)[0]
            for prop in dir(cls) if prop.startswith('_') is False
        }

    if out == 'tuple':
        d = list(d.items())
        # Keep tuple consistent so when migration runs it won't detect its changes
        d.sort(key=lambda x: x[0])
    elif out == 'list':
        return sorted(list(d.keys()))

    return d


def round_off(value, digits=2):
    """
    Rounding off the value

    :param float value: Value to be rounded
    :param digits: Digit to kept as after point
    :return float: Rounded value
    """
    return float(("{0:.%sf}" % digits).format(value))


def camel_to_snake_case(name):
    """
    Converts given camel cased string to snake case

    For eg:
        - CamelCamelCase -> camel_camel_case
        - Camel2Camel2Case -> camel2_camel2_case
        - get2HTTPResponseCode -> get2_http_response_code

    :param str name: String to be converted
    :return str: Converted string
    """
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower().replace(' ', '_')


def snake_case_to_title(s):
    """
    Converts snake case string to title case

    :param str s: String to be converted
    :return str: Converted string
    """
    return s.replace('_', ' ').title().replace(' ', '')


def strip_dict(d):
    return {k: v.strip() if isinstance(v, str) else v for k, v in d.items()}


def utc_to_local_time(t, to_tz, fmt='%H:%M'):
    utc_tz = pytz.timezone('UTC')
    local_tz = pytz.timezone(to_tz)

    dt = datetime.datetime.combine(datetime.date.today(), t)
    local_dt = utc_tz.localize(dt).astimezone(local_tz)
    if fmt is None:
        return local_dt.time()
    return local_dt.strftime(fmt)


@contextmanager
def redis_lock(key, timeout=None):
    lock = cache.lock(key, timeout=timeout)
    if not lock.acquire(blocking=False):
        raise err.LockError('Cannot acquire the lock. The same job might be in progress.')

    def _release_lock():
        try:
            lock.release()
        except Exception:
            pass

    try:
        yield
    except Exception:
        _release_lock()
        raise

    _release_lock()


def path_leaf(path):
    """
    Extracts file name from given path

    :param str path: Path be extracted the file name from
    :return str: File name
    """
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class Constant(str):
    def __new__(cls, value, *args, **kwargs):
        # explicitly only pass value to the str constructor
        return str.__new__(cls, value)

    def __init__(self, value, help_text=''):
        self.value = value
        self.text = help_text

    def __str__(self):
        return self.value

    def __iter__(self):
        yield self.value
        yield self.text

    def __getitem__(self, item):
        if item == 0:
            return self.value
        elif item == 1:
            return self.text
        else:
            raise IndexError()

            
def flatten_dict(d, parent_key='', sep='.'):
    items = []

    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)