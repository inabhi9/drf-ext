import factory

from drf_ext.faker import fake
from drf_ext.notification.models import Notification


class NonRelMixin(factory.BaseDictFactory):
    title = fake.text(max_nb_chars=50)
    description = fake.text(max_nb_chars=200)


class NotificationFactory(factory.DjangoModelFactory, NonRelMixin):
    class Meta:
        model = Notification

    @factory.post_generation
    def to_users(self, created, extracted, **kwargs):
        if not created:
            return

        if extracted is not None:
            self.to_users.add(*extracted)

    @factory.post_generation
    def to_groups(self, created, extracted, **kwargs):
        if not created:
            return

        if extracted is not None:
            self.to_groups.add(*extracted)

    @factory.post_generation
    def to_contacts(self, created, extracted, **kw):
        if not created:
            return

        if extracted is not None:
            self.to_contacts.add(*extracted)
