from django.contrib.auth.models import Group
from django.urls import reverse

from mailings.models import Attempt, Client, Mailing, MailingRun, Message
from mailings.tests.helpers import BaseTestCase, make_client, make_mailing, make_user

FORMSET_EMPTY = {
    'clients-TOTAL_FORMS': '0',
    'clients-INITIAL_FORMS': '0',
    'clients-MIN_NUM_FORMS': '0',
    'clients-MAX_NUM_FORMS': '1000',
}


def mailing_post_data(client_ids, **overrides):
    data = {
        'first_send_at': '2030-01-01T10:00',
        'end_send_at': '2030-02-01T10:00',
        'periodicity': Mailing.Frequency.DAILY,
        'clients': client_ids,
        'subject': 'Тема',
        'body': 'Текст',
    }
    data.update(overrides)
    return data


class MailingViewsTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = make_user('owner@example.com')
        self.other = make_user('other@example.com')
        self.recipient = make_client('recipient@example.com')
        self.mailing = make_mailing(self.owner, [self.recipient])

    def test_list_requires_login(self):
        response = self.client.get(reverse('mailings:mailing_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_list_shows_only_own_mailings(self):
        foreign = make_mailing(self.other)
        self.client.force_login(self.owner)

        response = self.client.get(reverse('mailings:mailing_list'))

        self.assertEqual(response.status_code, 200)
        objects = list(response.context['object_list'])
        self.assertIn(self.mailing, objects)
        self.assertNotIn(foreign, objects)

    def test_create_page_opens_for_logged_in_user(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('mailings:mailing_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_saves_mailing_with_owner_and_message(self):
        self.client.force_login(self.other)
        data = {**mailing_post_data([self.recipient.pk]), **FORMSET_EMPTY}

        response = self.client.post(reverse('mailings:mailing_create'), data)

        self.assertRedirects(response, reverse('mailings:mailing_list'))
        mailing = Mailing.objects.get(owner=self.other)
        self.assertEqual(mailing.message.subject, 'Тема')
        self.assertEqual(mailing.next_send_at, mailing.first_send_at)

    def test_create_adds_new_client_from_formset(self):
        self.client.force_login(self.other)
        data = {
            **mailing_post_data([self.recipient.pk]),
            **FORMSET_EMPTY,
            'clients-TOTAL_FORMS': '1',
            'clients-0-id': '',
            'clients-0-email': 'new@example.com',
            'clients-0-full_name': 'Новый',
            'clients-0-comment': '',
        }

        self.client.post(reverse('mailings:mailing_create'), data)

        mailing = Mailing.objects.get(owner=self.other)
        self.assertTrue(Client.objects.filter(email='new@example.com').exists())
        self.assertEqual(mailing.clients.count(), 2)

    def test_create_with_invalid_dates_does_not_save(self):
        self.client.force_login(self.other)
        data = {
            **mailing_post_data([self.recipient.pk], end_send_at='2029-01-01T10:00'),
            **FORMSET_EMPTY,
        }

        response = self.client.post(reverse('mailings:mailing_create'), data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Mailing.objects.filter(owner=self.other).exists())

    def test_detail_available_to_owner(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('mailings:mailing_detail', args=[self.mailing.pk]))
        self.assertEqual(response.status_code, 200)

    def test_detail_forbidden_for_other_user(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('mailings:mailing_detail', args=[self.mailing.pk]))
        self.assertEqual(response.status_code, 403)

    def test_detail_redirects_anonymous_to_login(self):
        response = self.client.get(reverse('mailings:mailing_detail', args=[self.mailing.pk]))
        self.assertEqual(response.status_code, 302)

    def test_detail_shows_runs_with_counters(self):
        run = MailingRun.objects.create(mailing=self.mailing)
        Attempt.objects.create(mailing=self.mailing, client=self.recipient, run=run,
                               status=Attempt.Status.SUCCESS)
        self.client.force_login(self.owner)

        response = self.client.get(reverse('mailings:mailing_detail', args=[self.mailing.pk]))

        runs = response.context['runs']
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].success_count, 1)
        self.assertEqual(runs[0].failed_count, 0)

    def test_update_by_owner_changes_message_and_redirects_to_detail(self):
        self.client.force_login(self.owner)
        data = mailing_post_data([self.recipient.pk], subject='Обновлённая')

        response = self.client.post(reverse('mailings:mailing_update', args=[self.mailing.pk]), data)

        self.assertRedirects(response, reverse('mailings:mailing_detail', args=[self.mailing.pk]))
        self.mailing.message.refresh_from_db()
        self.assertEqual(self.mailing.message.subject, 'Обновлённая')

    def test_update_forbidden_for_other_user(self):
        self.client.force_login(self.other)
        data = mailing_post_data([self.recipient.pk], subject='Взлом')

        response = self.client.post(reverse('mailings:mailing_update', args=[self.mailing.pk]), data)

        self.assertEqual(response.status_code, 403)
        self.mailing.message.refresh_from_db()
        self.assertNotEqual(self.mailing.message.subject, 'Взлом')

    def test_delete_by_owner_removes_mailing_and_message(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('mailings:mailing_delete', args=[self.mailing.pk]))

        self.assertRedirects(response, reverse('mailings:mailing_list'))
        self.assertFalse(Mailing.objects.filter(pk=self.mailing.pk).exists())
        self.assertEqual(Message.objects.count(), 0)

    def test_delete_forbidden_for_other_user(self):
        self.client.force_login(self.other)

        response = self.client.post(reverse('mailings:mailing_delete', args=[self.mailing.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Mailing.objects.filter(pk=self.mailing.pk).exists())


class RunViewsTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.owner = make_user('owner@example.com')
        self.other = make_user('other@example.com')
        self.recipient = make_client()
        self.mailing = make_mailing(self.owner, [self.recipient])
        self.run = MailingRun.objects.create(mailing=self.mailing)
        Attempt.objects.create(mailing=self.mailing, client=self.recipient, run=self.run,
                               status=Attempt.Status.FAILED, answer='ошибка')

    def test_run_detail_for_owner_lists_attempts(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('mailings:run_detail', args=[self.run.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['attempts']), 1)

    def test_run_detail_is_hidden_from_other_user(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('mailings:run_detail', args=[self.run.pk]))
        self.assertEqual(response.status_code, 404)

    def test_run_list_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('mailings:mailing_runs', args=[self.mailing.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['object_list']), [self.run])

    def test_run_list_is_hidden_from_other_user(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('mailings:mailing_runs', args=[self.mailing.pk]))
        self.assertEqual(response.status_code, 404)


class ClientViewsTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user('user@example.com')
        self.manager = make_user('manager@example.com')
        group, _ = Group.objects.get_or_create(name='managers')
        self.manager.groups.add(group)
        self.recipient = make_client('recipient@example.com', full_name='Получатель')

    def test_any_logged_in_user_can_create_client(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('mailings:client_create'), {
            'full_name': 'Новый', 'email': 'new@example.com', 'comment': '',
        })

        self.assertRedirects(response, reverse('mailings:client_create'))
        self.assertTrue(Client.objects.filter(email='new@example.com').exists())

    def test_create_client_requires_login(self):
        response = self.client.get(reverse('mailings:client_create'))
        self.assertEqual(response.status_code, 302)

    def test_manager_sees_client_list(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('mailings:client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.recipient, response.context['object_list'])

    def test_regular_user_cannot_see_client_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('mailings:client_list'))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_from_client_list(self):
        response = self.client.get(reverse('mailings:client_list'))
        self.assertEqual(response.status_code, 302)

    def test_manager_sees_client_detail(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('mailings:client_detail', args=[self.recipient.pk]))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_update_client(self):
        self.client.force_login(self.manager)

        response = self.client.post(reverse('mailings:client_update', args=[self.recipient.pk]), {
            'full_name': 'Переименован', 'email': 'recipient@example.com', 'comment': '',
        })

        self.assertEqual(response.status_code, 302)
        self.recipient.refresh_from_db()
        self.assertEqual(self.recipient.full_name, 'Переименован')

    def test_regular_user_cannot_update_client(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('mailings:client_update', args=[self.recipient.pk]), {
            'full_name': 'Взлом', 'email': 'recipient@example.com', 'comment': '',
        })
        self.assertEqual(response.status_code, 403)

    def test_manager_can_delete_client_via_post(self):
        self.client.force_login(self.manager)

        response = self.client.post(reverse('mailings:client_delete', args=[self.recipient.pk]))

        self.assertRedirects(response, reverse('mailings:client_list'))
        self.assertFalse(Client.objects.filter(pk=self.recipient.pk).exists())

    def test_delete_client_does_not_allow_get(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('mailings:client_delete', args=[self.recipient.pk]))
        self.assertEqual(response.status_code, 405)

    def test_regular_user_cannot_delete_client(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('mailings:client_delete', args=[self.recipient.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Client.objects.filter(pk=self.recipient.pk).exists())
