from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
import secrets
from users.forms import UserCreateForm
from users.models import User
from users.services import send_confirmation_email



class RegisterView(CreateView):
    model = User
    form_class = UserCreateForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_active = False
        self.object.generate_confirmation_token()
        self.object.save()
        send_confirmation_email(self.object)
        return redirect(self.get_success_url())


def confirm_email(request, token):
    user = get_object_or_404(User, token=token)
    if not user.is_token_valid():
        return render(request, 'users/token_expired.html', status=400)
    user.confirm()
    return redirect('users:login')