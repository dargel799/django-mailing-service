from datetime import timedelta
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from mailings.models import Client, Mailing, Message
from users.models import User


LOCMEM_CACHE = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
}


@override_settings(CACHES=LOCMEM_CACHE)
class BaseTestCase(TestCase):

    def setUp(self):
        super().setUp()
        cache.clear()


def make_user(email='user@example.com', password='pass12345', **extra):
    user = User(email=email, full_name=extra.pop('full_name', 'Test User'), **extra)
    user.set_password(password)
    user.save()
    return user


def make_client(email='client@example.com', **extra):
    return Client.objects.create(email=email, **extra)


def make_mailing(owner, clients=(), *, subject='Тема', body='Текст',
                 next_send_in=timedelta(minutes=-1), duration=timedelta(days=10),
                 periodicity=Mailing.Frequency.DAILY, status=Mailing.Status.CREATED):
    now = timezone.now()
    message = Message.objects.create(subject=subject, body=body)
    mailing = Mailing.objects.create(
        first_send_at=now + next_send_in,
        next_send_at=now + next_send_in,
        end_send_at=now + duration,
        periodicity=periodicity,
        status=status,
        message=message,
        owner=owner,
    )
    mailing.clients.set(clients)
    return mailing
