from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from users.models import User

PASSWORD = 'Sup3r-secret-pass'


def make_user(email='user@example.com', **extra):
    user = User(email=email, full_name='Вася', **extra)
    user.set_password(PASSWORD)
    user.save()
    return user


@override_settings(SITE_DOMAIN='testserver')
class RegisterViewTests(TestCase):
    def register_data(self, **overrides):
        data = {
            'full_name': 'Вася',
            'email': 'new@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        }
        data.update(overrides)
        return data

    def test_register_page_opens(self):
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_inactive_user_with_token(self):
        response = self.client.post(reverse('users:register'), self.register_data())

        self.assertRedirects(response, reverse('users:login'))
        user = User.objects.get(email='new@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(len(user.token), 32)

    def test_register_sends_confirmation_email_with_link(self):
        self.client.post(reverse('users:register'), self.register_data())

        user = User.objects.get(email='new@example.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['new@example.com'])
        link = reverse('users:confirm_email', kwargs={'token': user.token})
        self.assertIn(link, mail.outbox[0].body)

    def test_register_with_different_passwords_creates_nothing(self):
        response = self.client.post(
            reverse('users:register'), self.register_data(password2='другой-пароль'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_register_with_existing_email_is_rejected(self):
        make_user('new@example.com')

        response = self.client.post(reverse('users:register'), self.register_data())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='new@example.com').count(), 1)


class ConfirmEmailTests(TestCase):
    def make_unconfirmed_user(self):
        user = make_user(is_active=False)
        user.generate_confirmation_token()
        user.save()
        return user

    def test_valid_token_activates_user(self):
        user = self.make_unconfirmed_user()

        response = self.client.get(reverse('users:confirm_email', kwargs={'token': user.token}))

        self.assertRedirects(response, reverse('users:login'))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.token)

    def test_expired_token_returns_400_and_keeps_user_inactive(self):
        user = self.make_unconfirmed_user()
        user.token_created_at = timezone.now() - timedelta(hours=25)
        user.save()

        response = self.client.get(reverse('users:confirm_email', kwargs={'token': user.token}))

        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_unknown_token_returns_404(self):
        response = self.client.get(reverse('users:confirm_email', kwargs={'token': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)


class LoginLogoutTests(TestCase):
    def login(self, email='user@example.com', password=PASSWORD):
        return self.client.post(reverse('users:login'), {'username': email, 'password': password})

    def test_active_user_can_log_in(self):
        make_user()

        response = self.login()

        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_wrong_password_is_rejected(self):
        make_user()

        response = self.login(password='неверный')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_unconfirmed_user_cannot_log_in_and_sees_hint(self):
        make_user(is_active=False)

        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        errors = ' '.join(response.context['form'].non_field_errors())
        self.assertIn('не подтверждён', errors)

    def test_logout_via_post(self):
        self.client.force_login(make_user())

        response = self.client.post(reverse('users:logout'))

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
