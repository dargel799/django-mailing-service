from django.urls import path

from mailings.apps import MailingsConfig
from mailings.models import Message
from mailings.views import MessageListView, MessageCreateView, MailingListView

app_name = MailingsConfig.name

urlpatterns = [
    path('', MailingListView.as_view(), name='mailing-list'),
    path('massage/create/', MessageCreateView.as_view(), name='massage_create')
]