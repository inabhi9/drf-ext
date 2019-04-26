import logging
from itertools import chain

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.postgres import fields as pg_fields
from django.db import models, transaction
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.db.models.query import QuerySet

from drf_ext.db.models import Manager, Model
from drf_ext.notification.mediums import Pusher
from . import signals
from .emailer import EmailNotification

L = logging.getLogger('drf_ext.' + __name__)


class NotificationManager(Manager):
    @transaction.atomic
    def create(self, **kwargs):
        """ Overriding method to add ManyToMany fields as well """
        to_users = kwargs.pop('to_users', [])
        to_groups = kwargs.pop('to_groups', [])
        nosignal = kwargs.pop('nosignal', False)

        notification = super(NotificationManager, self).create(**kwargs)
        # Adding many to many fields
        notification.to_users.add(*to_users)
        notification.to_groups.add(*to_groups)

        if nosignal is False:
            signals.new_notification.send(instance=notification)

        return notification

    def send(self, mediums, **kwargs):
        assert any([medium in ('email', 'pusher') for medium in mediums])

        with transaction.atomic():
            notification = self.create(**kwargs)
            try:
                notification.send(mediums)
                notification.delete()
            except:
                notification.delete()
                raise

    def mark_all_as_read(self, user):
        """
        Mark notifications as read for the user

        :param User user: The user, notification should be marked as read for
        :return int:
        """
        return (self.only_unread(user.id)
                .update(read_by_user_ids=RawSQL('read_by_user_ids || %s', [user.id])))


class NotificationQuerySet(QuerySet):
    def only_unread(self, user_id):
        """
        Filter queryset by notifications which are not read by the user
        """
        return self.filter(~Q(read_by_user_ids__contains=[user_id]))


class AbstractNotification(Model):
    """
    Class to store notifications sending to the user
    """
    #: Title of the notification, ie Subject
    title = models.CharField(max_length=75)
    #: Additional description to be included
    description = models.CharField(max_length=1000, blank=True, default='')
    #: Type of notification
    kind = models.CharField(max_length=50)
    #: Users who are supposed to receive notification
    to_users = models.ManyToManyField(get_user_model(), related_name='+', blank=True)
    #: Groups those supposed to receive notification
    to_groups = models.ManyToManyField(Group, blank=True)
    #: Arbitrary email to be sent to
    to_emails = pg_fields.ArrayField(models.EmailField(), default=list, blank=True)
    #: Any additional data
    extra = pg_fields.JSONField(blank=True, null=True, default=None)
    #: Any additional data that needs to be kept secret from exposing through API
    secret = pg_fields.JSONField(blank=True, null=True, default=None)
    #: Owner of the notification, i.e sender
    owner = models.ForeignKey(get_user_model(), null=True, on_delete=models.SET_NULL)
    read_by_user_ids = pg_fields.ArrayField(models.PositiveIntegerField(), default=list,
                                            blank=True, editable=False)

    objects = NotificationManager.from_queryset(NotificationQuerySet)()

    emailer = EmailNotification()
    pusher = Pusher()

    class Meta(Model.Meta):
        abstract = True
        db_table = 'notification'
        ordering = ('-id',)
        default_permissions = ('add', 'view', 'delete')

    def send(self, mediums=('email',)):
        L.info('Sending notification to users and groups')

        if 'email' in mediums:
            res = self.emailer.send(self)
            L.info('Sent notification through email. Result: (%s) for %s', res, self)

        if 'pusher' in mediums:
            self.pusher.notification = self
            res = self.pusher.send()
            L.info('Sent notification through pusher. Result: (%s) for %s', res, self)

    def get_all_users(self):
        """ Get all users included in this notification """
        users = [self.to_users.all()]

        gq = Q()
        for group in self.to_groups.all():
            gq |= Q(groups=group)
        if len(gq) > 0:
            users.append(get_user_model().objects.filter(gq).all())

        return list(set(chain(*users)))

    def __str__(self):
        return '%s (%s)' % (self.title, self.id)
