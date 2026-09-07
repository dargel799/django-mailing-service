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
        """Создаёт неактивного пользователя и отправляет письмо для подтверждения почты."""
        form.instance.is_active = False
        form.instance.generate_confirmation_token()
        response = super().form_valid(form)
        send_confirmation_email(self.object)
        return response


def confirm_email(request, token):
    """Подтверждает почту пользователя по токену из письма и активирует его аккаунт."""
    user = get_object_or_404(User, token=token)
    if not user.is_token_valid():
        return render(request, 'users/token_expired.html', status=400)
    user.confirm()
    return redirect('users:login')