from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command

from mailings.services import MailingRunReport
from mailings.tasks import dispatch_due_mailings, send_mailing_task
from mailings.tests.helpers import BaseTestCase, make_client, make_mailing, make_user


class SendMailingTaskTests(BaseTestCase):
    @patch('mailings.tasks.send_mailing', return_value=MailingRunReport(sent_count=2, failed_count=1))
    def test_returns_counters_from_report(self, _send_mailing):
        self.assertEqual(send_mailing_task(1), {'sent': 2, 'failed': 1})

    def test_unknown_mailing_does_not_raise_and_is_logged(self):
        with self.assertLogs('mailings.tasks', level='WARNING'):
            result = send_mailing_task(999999)

        self.assertEqual(result, {'sent': 0, 'failed': 0})

    def test_really_sends_mail(self):
        mailing = make_mailing(make_user(), [make_client()])

        result = send_mailing_task(mailing.pk)

        self.assertEqual(result, {'sent': 1, 'failed': 0})
        self.assertEqual(len(mail.outbox), 1)


class DispatchDueMailingsTests(BaseTestCase):
    def test_queues_task_only_for_due_mailings(self):
        owner = make_user()
        due = make_mailing(owner)
        make_mailing(owner, next_send_in=timedelta(hours=1))

        with patch.object(send_mailing_task, 'delay') as delay:
            queued = dispatch_due_mailings()

        self.assertEqual(queued, 1)
        delay.assert_called_once_with(due.pk)

    def test_nothing_due_queues_nothing(self):
        with patch.object(send_mailing_task, 'delay') as delay:
            queued = dispatch_due_mailings()

        self.assertEqual(queued, 0)
        delay.assert_not_called()


class SendMailingsCommandTests(BaseTestCase):
    def test_command_sends_due_mailings_and_prints_summary(self):
        make_mailing(make_user(), [make_client()])
        out = StringIO()

        call_command('send_mailings', stdout=out)

        self.assertIn('отправлено: 1', out.getvalue())
        self.assertEqual(len(mail.outbox), 1)
