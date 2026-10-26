from django.db import IntegrityError, transaction

from mailings.models import Attempt, Mailing, MailingRun, Message
from mailings.tests.helpers import BaseTestCase, make_client, make_mailing, make_user


class ClientModelTests(BaseTestCase):
    def test_str(self):
        client = make_client('a@example.com', full_name='Иван Иванов')
        self.assertEqual(str(client), 'Иван Иванов: a@example.com')

    def test_email_is_unique(self):
        make_client('a@example.com')
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_client('a@example.com')


class MessageModelTests(BaseTestCase):
    def test_str_returns_subject(self):
        self.assertEqual(str(Message(subject='Привет', body='...')), 'Привет')


class MailingModelTests(BaseTestCase):
    def test_default_status_is_created(self):
        mailing = make_mailing(make_user())
        self.assertEqual(mailing.status, Mailing.Status.CREATED)

    def test_deleting_mailing_deletes_runs_and_attempts(self):
        client = make_client()
        mailing = make_mailing(make_user(), [client])
        run = MailingRun.objects.create(mailing=mailing)
        Attempt.objects.create(mailing=mailing, client=client, run=run, status=Attempt.Status.SUCCESS)

        mailing.delete()

        self.assertEqual(MailingRun.objects.count(), 0)
        self.assertEqual(Attempt.objects.count(), 0)

    def test_deleting_client_keeps_attempt(self):
        client = make_client()
        mailing = make_mailing(make_user(), [client])
        run = MailingRun.objects.create(mailing=mailing)
        attempt = Attempt.objects.create(
            mailing=mailing, client=client, run=run, status=Attempt.Status.FAILED,
        )

        client.delete()

        attempt.refresh_from_db()
        self.assertIsNone(attempt.client)


class MailingRunModelTests(BaseTestCase):
    def test_runs_are_ordered_newest_first(self):
        mailing = make_mailing(make_user())
        first = MailingRun.objects.create(mailing=mailing)
        second = MailingRun.objects.create(mailing=mailing)

        self.assertEqual(list(mailing.runs.all()), [second, first])
