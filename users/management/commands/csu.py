from users.models import User
from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Создает супер юзера'
    def handle(self, *args, **options):
        user = User(
            full_name='admin',
            email= os.getenv('ADMIN_EMAIL'),
            is_active = True,
            is_staff = True,
            is_superuser = True
        )
        user.set_password(os.getenv('ADMIN_PASSWORD'))
        user.save()