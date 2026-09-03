from django.core.mail import send_mail
from django.urls import reverse

from config import settings
from users.models import User

def send_confirmation_email(user: User):
    confirm_path = reverse('users:confirm_email', kwargs={'token': user.token})
    confirm_url = f'https://{settings.SITE_DOMAIN}{confirm_path}'
    message = f'Для регистрации профиля {user.username}, порейдите по ссылке: {confirm_url}',
    send_mail(
        subject='Подтверждение почты',
        message = f'Для регистрации профиля {user.username}, порейдите по ссылке: http://http://127.0.0.1:8000/users/confim-email/{user.token}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email]
    )