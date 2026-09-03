from django.contrib.auth.models import AbstractUser
from django.db import models
import secrets
from django.utils import timezone


class User(AbstractUser):
    username = None
    full_name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(unique=True, verbose_name='почта')
    avatar = models.ImageField(upload_to='avatars/', verbose_name='аватар', blank=True, null=True)
    description = models.TextField(verbose_name='описание', blank=True, null=True)
    token = models.CharField(max_length=32, null=True, blank=True, unique=True, verbose_name='токен')
    token_created_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def generate_confirmation_token(self):
        self.token = secrets.token_hex(16)
        self.token_created_at = timezone.now()



    def confirm(self):
        self.is_active = True
        self.token = None
        self.token_created_at = None
        self.save(update_fields=['is_active', 'token', 'token_created_at'])


    def is_token_valid(self, lifetime_hours=24):
        if not self.token_created_at:
            return False
        return timezone.now() < self.token_created_at + timezone.timedelta(hours=lifetime_hours)


    def __str__(self):
        return f'{self.full_name}: {self.email}'


    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'