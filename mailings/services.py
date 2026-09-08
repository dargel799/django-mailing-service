from dataclasses import dataclass

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import smtplib

from .models import Mailing, Attempt

FREQUENCY_DELTAS = {
    Mailing.Frequency.DAILY: relativedelta(days=1),
    Mailing.Frequency.WEEKLY: relativedelta(weeks=1),
    Mailing.Frequency.MONTHLY: relativedelta(months=1),
}


@dataclass
class MailingRunReport:
    """ Сводка результата одного вызова send_mailing."""

    sent_count: int = 0
    failed_count: int = 0


def send_mailing(pk: int) -> MailingRunReport:
    """Выполняет один цикл отправки рассылки."""

    mailing = (
        Mailing.objects
        .select_related('massage')
        .prefetch_related('clients')
        .get(pk=pk)
    )
    now = timezone.now()

    if mailing.status == Mailing.Status.FINISHED:
        return MailingRunReport()

    if mailing.end_send_at and now > mailing.end_send_at:
        mailing.status = Mailing.Status.FINISHED
        mailing.save(update_fields=['status'])
        return MailingRunReport()

    if now < mailing.next_send_at:
        return MailingRunReport()

    mailing.status = Mailing.Status.STARTED
    mailing.save(update_fields=['status'])

    attempts = []
    sent_count = 0
    failed_count = 0

    for client in mailing.clients.all():
        try:
            send_mail(
                mailing.message.subject,
                mailing.message.body,
                settings.EMAIL_HOST_USER,
                [client.email],
                fail_silently=False,
            )
        except smtplib.SMTPException as e:
            failed_count += 1
            attempts.append(Attempt(
                attempted_at=now,
                status=Attempt.Status.FAILED,
                answer=str(e),
                client=client,
                mailing=mailing,
            ))
        else:
            sent_count += 1
            attempts.append(Attempt(
                attempted_at=now,
                status=Attempt.Status.SUCCESS,
                answer='Письмо принято почтовым сервером',
                client=client,
                mailing=mailing,
            ))

    Attempt.objects.bulk_create(attempts)

    mailing.next_send_at = now + FREQUENCY_DELTAS[mailing.periodicity]
    mailing.save(update_fields=['next_send_at'])

    return MailingRunReport(sent_count=sent_count, failed_count=failed_count)


def process_mailings() -> list[MailingRunReport]:
    """Прогоняет через send_mailing не завершённе рассылки."""

    mailings = Mailing.objects.exclude(status=Mailing.Status.FINISHED)
    return [send_mailing(mailing.pk) for mailing in mailings]