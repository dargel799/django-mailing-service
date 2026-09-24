from users.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создает супер юзера'
    def handle(self, *args, **options):
        user = User(
            full_name='admin',
            email='admin@ya.pro',
            is_active = True,
            is_staff = True,
            is_superuser = True
        )
        user.set_password('admin')
        user.save()