from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from users.models import User


def make_user(**extra):
    user = User(email='user@example.com', full_name='Вася', **extra)
    user.set_password('pass12345')
    user.save()
    return user


class UserModelTests(TestCase):
    def test_str(self):
        self.assertEqual(str(make_user()), 'Вася: user@example.com')

    def test_email_is_login_field(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_generate_confirmation_token(self):
        user = make_user()
        user.generate_confirmation_token()

        self.assertEqual(len(user.token), 32)
        self.assertIsNotNone(user.token_created_at)

    def test_fresh_token_is_valid(self):
        user = make_user()
        user.generate_confirmation_token()
        self.assertTrue(user.is_token_valid())

    def test_old_token_is_invalid(self):
        user = make_user()
        user.generate_confirmation_token()
        user.token_created_at = timezone.now() - timedelta(hours=25)
        self.assertFalse(user.is_token_valid())

    def test_token_without_creation_date_is_invalid(self):
        self.assertFalse(make_user().is_token_valid())

    def test_confirm_activates_user_and_clears_token(self):
        user = make_user(is_active=False)
        user.generate_confirmation_token()
        user.save()

        user.confirm()

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.token)
        self.assertIsNone(user.token_created_at)
