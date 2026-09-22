from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView

from mailings.forms import MailingForm, ClientFormSet
from mailings.models import Message, Mailing, Client


class MessageListView(ListView):
    model = Message

class MessageCreateView(CreateView):
    model = Message
    fields = ['subject', 'body']
    success_url = reverse_lazy('mailings:mailing-list')


class MessageDetailView(DetailView):
    model = Message


class MessageUpdateView(UpdateView):
    model = Message
    success_url = reverse_lazy('mailings:mailing-list')


class MessageDeleteView(DeleteView):
    model = Message
    success_url = reverse_lazy('mailings:mailing-list')


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().owner == self.request.user


class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy('mailings:mailing_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['client_formset'] = ClientFormSet(
                self.request.POST,
                queryset=Client.objects.none(),
                prefix='clients',
            )
        else:
            context['client_formset'] = ClientFormSet(
                queryset=Client.objects.none(),
                prefix='clients',
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        client_formset = context['client_formset']

        if not client_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        form.instance.owner = self.request.user
        response = super().form_valid(form)

        new_clients = client_formset.save()
        if new_clients:
            self.object.clients.add(*new_clients)

        return response

class MailingDetailView(OwnerRequiredMixin, DetailView):
    model = Mailing


class MailingUpdateView(OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy('mailings:mailing_list')


class MailingDeleteView(OwnerRequiredMixin, DeleteView):
    model = Mailing
    success_url = reverse_lazy('mailings:mailing_list')