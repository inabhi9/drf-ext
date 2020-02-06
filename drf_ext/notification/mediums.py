import logging
import re

from django.conf import settings

L = logging.getLogger('drf_ext.' + __name__)


class AbstractMedium:
    notification = None
    _is_available = False

    def send(self):
        if self._is_available is False:
            L.error('%s medium is not available', self.__class__.__name__)
            return

        self.before_send()

        return self._send()

    def _send(self):
        raise NotImplementedError

    def before_send(self):
        pass


class Pusher(AbstractMedium):
    """
    Sending push notification through pusher.com service.

    Pusher limitations:
    * Batch requests are supported and limited to 10events per request in multi-cluster setup
    * Post request must be maximum of 10KB including a batch request.
    * Message count is applied when
        - HTTP request is made to the Pusher
        - Message delivered to the client
        - Webhook is called by Pusher
    """

    def __init__(self):
        try:
            import pusher

            self._app_id = settings.PUSHER_APP_ID
            self._key = settings.PUSHER_KEY
            self._secret = settings.PUSHER_SECRET
            self._cluster = settings.PUSHER_CLUSTER

            self._client = pusher.Pusher(
                app_id=self._app_id,
                key=self._key,
                secret=self._secret,
                cluster=self._cluster
            )
            self._is_available = True
        except (AttributeError, TypeError):
            L.warning('Pusher attributes are missing in the settings. Pusher will be unavailable.')
        except ImportError:
            L.warning('Pusher library is not installed. Pusher will be unavailable.')

    @property
    def client(self):
        return self._client

    @property
    def _event_name(self):
        return self.notification.kind

    @property
    def _body(self):
        d = {}

        if self.notification.title:
            d['title'] = self.notification.title
        if self.notification.description:
            d['description'] = self.notification.title

        extra = self.notification.extra or {}

        d.update(**extra)

        return d

    @property
    def _channels(self):
        channels = []

        if self.notification.to_users:
            user_ids = self.notification.to_users.values_list('id', flat=True).all()
            channels += ['user%s' % user_id for user_id in user_ids]

        if self.notification.to_groups:
            group_ids = self.notification.to_groups.values_list('id', flat=True).all()
            channels += ['group%s' % group_id for group_id in group_ids]

        if self.notification.to_emails:
            channels += list(map(lambda x: re.sub(r'@.*', '', x), self.notification.to_emails))

        return channels

    def _send(self):
        assert getattr(self, '_client', None) is not None

        cnt = 0

        for channels in self.__channels_batch:
            self.client.trigger(channels, self._event_name, self._body)
            cnt += len(channels)

        return cnt

    @property
    def __channels_batch(self):
        offset = 0
        limit = 100

        channels = self._channels

        while len(channels) > 0:
            channels = [channel if channel.startswith('private-') else 'private-%s' % channel
                        for channel in channels[offset: limit]]

            if len(channels) > 0:
                yield channels

            offset += limit
