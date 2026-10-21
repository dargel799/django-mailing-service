import logging

from celery import shared_task

from .models import Mailing
from .services import get_due_mailing_ids, send_mailing

logger = logging.getLogger(__name__)


@shared_task
def send_mailing_task(pk: int) -> dict:
    """Отправляет одну рассылку."""

    try:
        report = send_mailing(pk)
    except Mailing.DoesNotExist:
        logger.warning('Рассылка %s не найдена (возможно, удалена)', pk)
        return {'sent': 0, 'failed': 0}

    logger.info('Рассылка %s: отправлено %s, ошибок %s', pk, report.sent_count, report.failed_count)
    return {'sent': report.sent_count, 'failed': report.failed_count}


@shared_task
def dispatch_due_mailings() -> int:
    """Периодическая задача celery beat
    раз в минуту находит подошедшие рассылки и ставит по задаче на каждую."""

    ids = get_due_mailing_ids()
    for pk in ids:
        send_mailing_task.delay(pk)
    return len(ids)