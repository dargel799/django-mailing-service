from django.core.management.base import BaseCommand

from mailings.services import process_mailings


class Command(BaseCommand):
    help = 'Отправляет рассылки, время которых наступило'

    def handle(self, *args, **options):
        reports = process_mailings()
        sent = sum(r.sent_count for r in reports)
        failed = sum(r.failed_count for r in reports)
        self.stdout.write(self.style.SUCCESS(
            f'Проверено рассылок: {len(reports)}, отправлено: {sent}, ошибок: {failed}'
        ))