from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView
from mailings.permissions import OwnerRequiredMixin, ManagersRequiredMixin
from mailings.forms import MailingForm, ClientFormSet, ClientForm
from mailings.models import Mailing, Client, MailingRun, Attempt
from django.db.models import Count, Q

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
        form.instance.next_send_at = form.instance.first_send_at
        response = super().form_valid(form)

        new_clients = client_formset.save()
        if new_clients:
            self.object.clients.add(*new_clients)

        return response

class MailingDetailView(OwnerRequiredMixin, DetailView):
    model = Mailing

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cache_key = f'mailing_runs_{self.object.pk}'
        runs = cache.get(cache_key)
        if runs is None:
            runs = list(
                self.object.runs
                .annotate(
                    success_count=Count('attempts', filter=Q(attempts__status=Attempt.Status.SUCCESS)),
                    failed_count=Count('attempts', filter=Q(attempts__status=Attempt.Status.FAILED)),
                )
                .order_by('-started_at')[:10]
            )
            cache.set(cache_key, runs, timeout=60)

        context['runs'] = runs
        return context



class MailingUpdateView(OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm

    def get_success_url(self):
        return reverse('mailings:mailing_detail', kwargs={'pk': self.object.pk})


class MailingDeleteView(OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailings/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def form_valid(self, form):
        self.object = self.get_object()
        message = self.object.message
        response = super().form_valid(form)
        message.delete()
        return response


class RunDetailView(LoginRequiredMixin, DetailView):
    model = MailingRun
    template_name = 'mailings/run_detail.html'

    def get_queryset(self):
        return MailingRun.objects.filter(mailing__owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cache_key = f'run_attempts_{self.object.pk}'
        attempts = cache.get(cache_key)
        if attempts is None:
            attempts = list(
                self.object.attempts.select_related('client').order_by('client__email')
            )
            cache.set(cache_key, attempts, timeout=60*60*12)

        context['attempts'] = attempts
        return context

class RunListView(LoginRequiredMixin, ListView):
    model = MailingRun
    template_name = 'mailings/run_list.html'
    paginate_by = 20

    def get_queryset(self):
        self.mailing = get_object_or_404(
            Mailing, pk=self.kwargs['pk'], owner=self.request.user
        )
        return (
            self.mailing.runs
            .annotate(
                success_count=Count('attempts', filter=Q(attempts__status=Attempt.Status.SUCCESS)),
                failed_count=Count('attempts', filter=Q(attempts__status=Attempt.Status.FAILED)),
            )
            .order_by('-started_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mailing'] = self.mailing
        return context

class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailings/client_form.html'
    success_url = reverse_lazy('mailings:client_create')


class ClientDeleteView(ManagersRequiredMixin, DeleteView):
    model = Client
    success_url = reverse_lazy('mailings:client_list')
    http_method_names = ['post']


class ClientListView(ManagersRequiredMixin, ListView):
    model = Client
    template_name = 'mailings/client_list.html'


class ClientDetailView(ManagersRequiredMixin, DetailView):
    model = Client
    template_name = 'mailings/client_detail.html'


class ClientUpdateView(ManagersRequiredMixin, UpdateView):
    model = Client
    fields = ['email', 'full_name', 'comment']
    success_url = reverse_lazy('mailings:mailing_list')