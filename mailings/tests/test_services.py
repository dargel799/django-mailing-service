from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.utils import timezone

from mailings.models import Attempt, Mailing, MailingRun
from mailings.services import (
    compute_next_send_at,
    get_due_mailing_ids,
    process_mailings,
    send_mailing,
)
from mailings.tests.helpers import BaseTestCase, make_client, make_mailing, make_user


class ComputeNextSendAtTests(BaseTestCase):
    def test_future_first_send_is_returned_as_is(self):
        first = timezone.now() + timedelta(days=3)
        self.assertEqual(compute_next_send_at(first, Mailing.Frequency.DAILY), first)

    def test_daily_steps_to_next_future_slot(self):
        first = timezone.now() - timedelta(days=2, hours=12)
        result = compute_next_send_at(first, Mailing.Frequency.DAILY)
        self.assertEqual(result, first + timedelta(days=3))

    def test_weekly_steps_to_next_future_slot(self):
        first = timezone.now() - timedelta(days=10)
        result = compute_next_send_at(first, Mailing.Frequency.WEEKLY)
        self.assertEqual(result, first + timedelta(weeks=2))

    def test_monthly_result_is_within_a_month_from_now(self):
        now = timezone.now()
        result = compute_next_send_at(now - timedelta(days=45), Mailing.Frequency.MONTHLY)
        self.assertGreater(result, now)
        self.assertLessEqual(result, now + timedelta(days=32))


class SendMailingTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = make_user()
        self.clients = [make_client('a@example.com'), make_client('b@example.com')]

    def test_sends_to_every_client_and_records_attempts(self):
        mailing = make_mailing(self.owner, self.clients, subject='Скидки', body='Привет!')

        report = send_mailing(mailing.pk)

        self.assertEqual((report.sent_count, report.failed_count), (2, 0))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual({m.subject for m in mail.outbox}, {'Скидки'})
        self.assertEqual(MailingRun.objects.filter(mailing=mailing).count(), 1)
        attempts = Attempt.objects.filter(mailing=mailing)
        self.assertEqual(attempts.count(), 2)
        self.assertTrue(all(a.status == Attempt.Status.SUCCESS for a in attempts))

    def test_moves_next_send_at_forward_and_sets_started(self):
        mailing = make_mailing(self.owner, self.clients)
        old_next = mailing.next_send_at

        send_mailing(mailing.pk)

        mailing.refresh_from_db()
        self.assertEqual(mailing.status, Mailing.Status.STARTED)
        self.assertEqual(mailing.next_send_at, old_next + timedelta(days=1))

    def test_does_nothing_before_send_time(self):
        mailing = make_mailing(self.owner, self.clients, next_send_in=timedelta(hours=1))

        report = send_mailing(mailing.pk)

        self.assertEqual((report.sent_count, report.failed_count), (0, 0))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(MailingRun.objects.count(), 0)

    def test_finishes_mailing_after_end_date_without_sending(self):
        mailing = make_mailing(
            self.owner, self.clients,
            next_send_in=timedelta(minutes=-10), duration=timedelta(minutes=-5),
        )

        report = send_mailing(mailing.pk)

        mailing.refresh_from_db()
        self.assertEqual(mailing.status, Mailing.Status.FINISHED)
        self.assertEqual(report.sent_count, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_finished_mailing_is_skipped(self):
        mailing = make_mailing(self.owner, self.clients, status=Mailing.Status.FINISHED)

        send_mailing(mailing.pk)

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(MailingRun.objects.count(), 0)

    def test_last_send_marks_mailing_finished(self):
        mailing = make_mailing(self.owner, self.clients, duration=timedelta(hours=1))

        send_mailing(mailing.pk)

        mailing.refresh_from_db()
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mailing.status, Mailing.Status.FINISHED)

    @patch('mailings.services.send_mail', side_effect=SMTPException('сервер недоступен'))
    def test_smtp_error_is_recorded_as_failed_attempt(self, _send_mail):
        mailing = make_mailing(self.owner, self.clients)

        report = send_mailing(mailing.pk)

        self.assertEqual((report.sent_count, report.failed_count), (0, 2))
        attempts = Attempt.objects.filter(mailing=mailing)
        self.assertTrue(all(a.status == Attempt.Status.FAILED for a in attempts))
        self.assertTrue(all('сервер недоступен' in a.answer for a in attempts))

    @patch('mailings.services.send_mail', side_effect=[1, SMTPException('ошибка')])
    def test_one_failure_does_not_stop_other_clients(self, _send_mail):
        mailing = make_mailing(self.owner, self.clients)

        report = send_mailing(mailing.pk)

        self.assertEqual((report.sent_count, report.failed_count), (1, 1))

    def test_unknown_mailing_raises(self):
        with self.assertRaises(Mailing.DoesNotExist):
            send_mailing(999999)

    def test_clears_cached_runs_of_mailing(self):
        mailing = make_mailing(self.owner, self.clients)
        cache.set(f'mailing_runs_{mailing.pk}', 'устаревшие данные')

        send_mailing(mailing.pk)

        self.assertIsNone(cache.get(f'mailing_runs_{mailing.pk}'))


class DueMailingsTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = make_user()

    def test_get_due_mailing_ids_selects_only_due_and_unfinished(self):
        due = make_mailing(self.owner)
        make_mailing(self.owner, next_send_in=timedelta(hours=1))
        make_mailing(self.owner, status=Mailing.Status.FINISHED)
        expired = make_mailing(
            self.owner, next_send_in=timedelta(hours=1), duration=timedelta(minutes=-1),
        )

        self.assertCountEqual(get_due_mailing_ids(), [due.pk, expired.pk])

    def test_process_mailings_returns_report_for_each_due_mailing(self):
        client = make_client()
        make_mailing(self.owner, [client])
        make_mailing(self.owner, [client], next_send_in=timedelta(hours=1))

        reports = process_mailings()

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].sent_count, 1)
