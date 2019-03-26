import logging
import os
import tempfile
from urllib import parse

import requests
from django.conf import settings
from django.core.mail import EmailMessage

L = logging.getLogger('app.' + __name__)


class EmailNotification(object):
    """
    It uses Mandrill for sending emails.

    Before calling send() always set self.to_user attribute
    """
    to_user = None
    msg = None

    #: It'll use the mandrill template API and _send() function must have template_name args
    #: If it's set to false, from and subject must be set
    using_template = True

    def __init__(self, *args, **kwargs):
        pass

    def send(self, notification):
        """
        Triggers ``msg.send()``
        :param Notification notification: Notification object
        :param kwargs:
            :template_name: Template name
        :return:
        """
        self.msg = EmailMessage()
        self.to_user = None

        users = notification.get_all_users()
        extra = notification.extra or {}
        secret = notification.secret or {}
        to_emails = notification.to_emails or []

        extra.update(secret)
        bcc = users[1:] or []
        self.to_user = users[0] if len(users) > 0 else None
        if len(users) == 0 and len(to_emails) == 0:
            L.info('No users found to be sent')
            return

        # Merging user vars
        self.msg.merge_vars = getattr(self.msg, 'merge_vars', {})
        for user in users:
            if self.msg.merge_vars.get(user.email) is None:
                self.msg.merge_vars[user.email] = {}
            self.msg.merge_vars[user.email].update(**self._get_user_vars(user))

        # Merging global vars
        self.msg.global_merge_vars = dict(
            TITLE=notification.title,
            DESCRIPTION=notification.description,
            **extra
        )
        self.msg.global_merge_vars.update(**self._get_global_vars(notification))

        # Attachment
        files = self._attach_from_notification(notification)

        to_ = [self.to_user.email] if self.to_user else to_emails
        self.msg.to = to_
        self.msg.bcc = list(map(lambda u: u.email, bcc))
        self.msg.template_name = self._get_template_name(notification)
        self.msg.use_template_subject = True
        self.msg.use_template_from = True
        self.msg.merge_language = 'handlebars'
        self.msg.preserve_recipients = False
        self.msg.mandrill_response = None

        if notification.owner:
            self.msg.use_template_from = False
            self.msg.from_email = notification.owner.email
            self.msg.from_name = notification.owner.get_full_name()

        self.before_send(notification)

        self.msg.send()

        map(lambda f: os.unlink(f.name), files)

        return self.msg.mandrill_response

    def before_send(self, notification):
        pass

    @classmethod
    def _get_user_vars(cls, user_instance):
        return {
            'USER_EMAIL': user_instance.email,
            'USER_FIRST_NAME': user_instance.first_name,
            'USER_LAST_NAME': user_instance.last_name,
            'USER_EMAIL_ENCODED': parse.quote(user_instance.email),
        }

    @classmethod
    def _get_global_vars(cls, notification):
        return {'APP_WEB_URL': settings.APP_WEB_URL}

    @classmethod
    def _get_template_name(cls, notification):
        return settings.PROJECT_NAME + '-' + notification.kind

    def _attach_from_notification(self, notification):
        attachments = notification.extra.get('_attachments') if notification.extra else None
        files = []

        if isinstance(attachments, list):
            for attachment in attachments:
                filepath = None

                if os.path.isfile(attachment):
                    filepath = attachment
                elif attachment.startswith('http://') or attachment.startswith('https://'):
                    u = requests.get(attachment)
                    f = open(tempfile.gettempdir() + '/' + attachment.split('/')[-1], 'w+b')
                    files.append(f)
                    f.write(u.content)
                    f.close()
                    u.close()
                    filepath = f.name
                else:
                    continue

                self.msg.attach_file(filepath)

        return files
