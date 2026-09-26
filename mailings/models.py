from django.db import models

from users.models import User


OPTIONAL = {'null': True, 'blank': True}

class Client(models.Model):
    email = models.EmailField(verbose_name='контактный email', unique=True)
    full_name = models.CharField(max_length=100, **OPTIONAL, verbose_name='Ф. И. О.')
    comment = models.TextField(**OPTIONAL, verbose_name='комментарий')

    def __str__(self):
        return f'{self.full_name}: {self.email}'

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'


class Message(models.Model):
    subject = models.CharField(max_length=300, verbose_name='тема письма')
    body = models.TextField(verbose_name='тело письма')

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = 'Сообщение для рассылки'
        verbose_name_plural = 'Сообщения для рассылок'


class Attempt(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'success', 'успешно'
        FAILED = 'unsuccess', 'не успешно'


    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name='дата и время попытки')
    status = models.CharField(verbose_name='статус попытки', choices=Status.choices, max_length=max(len(i[0]) for i in Status.choices))
    answer = models.TextField(verbose_name='ответ почтового сервера', **OPTIONAL)
    mailing = models.ForeignKey('Mailing', related_name='attempts', on_delete=models.CASCADE, verbose_name='рассылка')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, related_name='attempts', **OPTIONAL)
    run = models.ForeignKey('MailingRun', related_name='attempts', on_delete=models.CASCADE, verbose_name='запуск рассылки')

    def __str__(self):
        return f'{self.attempted_at}: {self.status}'

    class Meta:
        verbose_name = 'попытка'
        verbose_name_plural = 'попытки'
        ordering = ('-attempted_at', 'mailing_id')

class Mailing(models.Model):

    class Frequency(models.TextChoices):
        DAILY = 'daily', 'раз в день'
        WEEKLY = 'weekly', 'раз в неделю'
        MONTHLY = 'monthly', 'раз в месяц'

    class Status(models.TextChoices):
        FINISHED = 'finished', 'завершена'
        CREATED = 'created', 'создана'
        STARTED = 'started', 'запущена'

    first_send_at = models.DateTimeField(verbose_name='дата и время первой отправки рассылки')
    next_send_at = models.DateTimeField(verbose_name='Дата и время следующий отправки')
    end_send_at = models.DateTimeField(verbose_name='Дата и время последней отправки')
    periodicity = models.CharField(max_length=max(len(i[0]) for i in Frequency.choices), choices=Frequency.choices, verbose_name='периодичность')
    status = models.CharField(max_length=max(len(i[0]) for i in Status.choices), choices=Status.choices, default=Status.CREATED, verbose_name='статус рассылки')
    message = models.OneToOneField(Message, on_delete=models.CASCADE, verbose_name='сообщение', related_name='mailings')
    clients = models.ManyToManyField('Client', related_name='mailings')
    owner = models.ForeignKey(User, related_name='mailings', verbose_name='владелец', on_delete=models.CASCADE)


class MailingRun(models.Model):
    mailing = models.ForeignKey(Mailing, related_name='runs', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='время запуска рассылки')

    class Meta:
        verbose_name = 'запуск рассылки'
        verbose_name_plural = 'запуски рассылки'
        ordering = ('-started_at',)

    def __str__(self):
        return f'{self.mailing}: {self.started_at}'
