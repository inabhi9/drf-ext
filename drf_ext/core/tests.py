import logging

from django.conf import settings
from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase, APIClient as _APIClient


class APIClient(_APIClient):
    def get(self, path, data=None, follow=False, **extra):
        response = super(APIClient, self).get(path, data=data, follow=follow, **extra)
        return self._fix_response(response)

    def post(self, path, data=None, format=None, content_type=None, follow=False, **extra):
        response = super(APIClient, self).post(path, data=data, format=format,
                                               content_type=content_type, follow=follow, **extra)

        return self._fix_response(response)

    def put(self, path, data=None, format=None, content_type=None, follow=False, **extra):
        response = super(APIClient, self).put(path, data=data, format=format,
                                              content_type=content_type, follow=follow, **extra)
        return self._fix_response(response)

    def delete(self, path, data=None, formatc=None, content_type=None, follow=False, **extra):
        response = super(APIClient, self).delete(path, data=data, format=format,
                                                 content_type=content_type, follow=follow, **extra)
        return self._fix_response(response)

    def patch(self, path, data=None, format=None, content_type=None, follow=False, **extra):
        response = super(APIClient, self).patch(path, data=data, format=format,
                                                content_type=content_type, follow=follow, **extra)
        return self._fix_response(response)

    @classmethod
    def _fix_response(cls, response):
        if response.get('Content-Type') != 'application/json':
            return response

        try:
            resp = response.json()
            response.meta = resp.get('meta')
            response.data = resp.get('data') or resp.get('error')
        except:
            pass

        return response


class TestCase(APITestCase):
    client_class = APIClient

    def __init__(self, methodName='runTest'):
        super(TestCase, self).__init__(methodName=methodName)

        # Disable logging
        logging.disable(logging.CRITICAL)

    def setUp(self):
        # Turning on debugging
        settings.DEBUG = True

        self.status_code = status

    def get_client(self, user, http_authorization_prefix='Token'):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION='%s %s' % (http_authorization_prefix, user.auth_token.key))
        return c

    def mock_timezone_now(self, time):
        self.patcher = patch('django.utils.timezone.now', lambda: time)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()
