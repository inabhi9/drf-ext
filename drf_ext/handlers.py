"""
========
Handlers
========
Holds logger handler classes
"""

from raven.contrib.django.raven_compat import handlers


class SentryHandler(handlers.SentryHandler):
    """
    Extends SentryHandler feature that adds thread id to record
    """

    def _emit(self, record):
        tags = getattr(record, 'tags', {})
        tags.update({
            'thread': record.thread
        })
        record.tags = tags

        return super(SentryHandler, self)._emit(record)
