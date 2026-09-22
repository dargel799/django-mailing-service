from django.urls import path
from django.views import View

from mailings.apps import MailingsConfig
from mailings.models import Message
from mailings.views import MessageListView, MessageCreateView, MailingListView, MailingCreateView, MailingDetailView, \
    MailingUpdateView, ClientCreateView, MailingDeleteView

app_name = MailingsConfig.name

urlpatterns = [
    path('', MailingListView.as_view(), name='mailing_list'),
    path('massage/create/', MessageCreateView.as_view(), name='massage_create'),
    path('create/', MailingCreateView.as_view(), name='mailing_create'),
    path('<int:pk>/', MailingDetailView.as_view(), name='mailing_detail'),
    path('update/<int:pk>', MailingUpdateView.as_view(), name='mailing_update'),
    path('clients/create/', ClientCreateView.as_view(), name='client_create'),
path('delete/<int:pk>', MailingDeleteView.as_view(), name='mailing_delete'),
]