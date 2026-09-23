from django.urls import path
from django.views import View

from mailings.apps import MailingsConfig
from mailings.views import MailingListView, MailingCreateView, MailingDetailView, \
    MailingUpdateView, ClientCreateView, MailingDeleteView, ClientListView, ClientDetailView, ClientUpdateView, \
    ClientDeleteView

app_name = MailingsConfig.name

urlpatterns = [
    path('', MailingListView.as_view(), name='mailing_list'),
    path('create/', MailingCreateView.as_view(), name='mailing_create'),
    path('<int:pk>/', MailingDetailView.as_view(), name='mailing_detail'),
    path('update/<int:pk>', MailingUpdateView.as_view(), name='mailing_update'),
    path('clients/create/', ClientCreateView.as_view(), name='client_create'),
path('delete/<int:pk>', MailingDeleteView.as_view(), name='mailing_delete'),
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:pk>/update/', ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
]