from . import factories
from ..tests import TestCase


class NotificationTest(TestCase):
    ENDPOINT = '/notifications'

    def test_create_simple_email(self):
        data = factories.NotificationDictFactory(kind='generic')
        resp = self.admin_client.post(self.ENDPOINT, data, format='json')

        self.assertEqual(resp.status_code, self.status_code.HTTP_201_CREATED)
