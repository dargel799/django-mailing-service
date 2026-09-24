from django.core.mail import send_mail
from django.urls import reverse

from django.conf import settings
from users.models import User

def send_confirmation_email(user: User):
    confirm_path = reverse('users:confirm_email', kwargs={'token': user.token})
    confirm_url = f'http://{settings.SITE_DOMAIN}{confirm_path}'
    message = f'Для регистрации профиля {user.full_name}, порейдите по ссылке: {confirm_url}'
    send_mail(
        subject='Подтверждение почты',
        message = message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email]
    )