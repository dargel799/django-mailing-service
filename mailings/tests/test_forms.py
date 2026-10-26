from django.utils import timezone

from mailings.forms import ClientForm, MailingForm
from mailings.models import Mailing, Message
from mailings.tests.helpers import BaseTestCase, make_client, make_mailing, make_user


class MailingFormTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = make_user()
        self.client_obj = make_client()

    def form_data(self, **overrides):
        data = {
            'first_send_at': '2030-01-01T10:00',
            'end_send_at': '2030-02-01T10:00',
            'periodicity': Mailing.Frequency.DAILY,
            'clients': [self.client_obj.pk],
            'subject': 'Привет',
            'body': 'Текст письма',
        }
        data.update(overrides)
        return data

    def test_valid_form_creates_message_and_mailing(self):
        form = MailingForm(self.form_data(), instance=Mailing(owner=self.owner))

        self.assertTrue(form.is_valid(), form.errors)
        mailing = form.save()

        self.assertEqual(mailing.message.subject, 'Привет')
        self.assertEqual(mailing.message.body, 'Текст письма')
        self.assertEqual(list(mailing.clients.all()), [self.client_obj])

    def test_future_first_send_becomes_next_send(self):
        form = MailingForm(self.form_data(), instance=Mailing(owner=self.owner))
        form.is_valid()
        mailing = form.save()

        self.assertEqual(mailing.next_send_at, mailing.first_send_at)

    def test_past_first_send_gives_future_next_send(self):
        data = self.form_data(first_send_at='2020-01-01T10:00', end_send_at='2035-01-01T10:00')
        form = MailingForm(data, instance=Mailing(owner=self.owner))
        form.is_valid()
        mailing = form.save()

        self.assertGreater(mailing.next_send_at, timezone.now())

    def test_end_date_must_be_after_first_date(self):
        data = self.form_data(end_send_at='2029-12-31T10:00')
        form = MailingForm(data, instance=Mailing(owner=self.owner))

        self.assertFalse(form.is_valid())
        self.assertIn('end_send_at', form.errors)

    def test_subject_and_body_are_required(self):
        form = MailingForm(self.form_data(subject='', body=''), instance=Mailing(owner=self.owner))

        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
        self.assertIn('body', form.errors)

    def test_edit_updates_existing_message_instead_of_creating_new(self):
        mailing = make_mailing(self.owner, [self.client_obj], subject='Старая', body='Старый')
        form = MailingForm(self.form_data(subject='Новая', body='Новый'), instance=mailing)

        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(Message.objects.count(), 1)
        mailing.message.refresh_from_db()
        self.assertEqual(mailing.message.subject, 'Новая')

    def test_edit_form_prefills_subject_and_body(self):
        mailing = make_mailing(self.owner, subject='Тема', body='Тело')
        form = MailingForm(instance=mailing)

        self.assertEqual(form.fields['subject'].initial, 'Тема')
        self.assertEqual(form.fields['body'].initial, 'Тело')


class ClientFormTests(BaseTestCase):
    def test_valid(self):
        form = ClientForm({'full_name': 'Иван', 'email': 'ivan@example.com', 'comment': ''})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email(self):
        form = ClientForm({'full_name': 'Иван', 'email': 'не-почта', 'comment': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email(self):
        make_client('ivan@example.com')
        form = ClientForm({'full_name': 'Другой', 'email': 'ivan@example.com', 'comment': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
