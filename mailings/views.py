from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView

from mailings.forms import MailingForm
from mailings.models import Message, Mailing


class MessageListView(ListView):
    model = Message

class MessageCreateView(CreateView):
    model = Message
    fields = ['subject', 'body']
    success_url = '/'
    

class MessageDetailView(DetailView):
    model = Message


class MessageUpdateView(UpdateView):
    model = Message
    success_url = '/'


class MessageDeleteView(DeleteView):
    model = Message
    success_url = '/'


class MailingListView(ListView):
    model = Mailing


class MailingCreateView(CreateView):
    model = Mailing
    form_class = MailingForm
    success_url = '/'


class MailingDetailView(DetailView):
    model = Mailing


class MailingUpdateView(UpdateView):
    model = Mailing
    success_url = '/'


class MailingDeleteView(DeleteView):
    model = Mailing
    success_url = '/'