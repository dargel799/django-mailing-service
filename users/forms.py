from django.contrib.auth.forms import UserCreationForm
from users.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'password1', 'password2']


class EmailAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'inactive': _("Ваш аккаунт не подтверждён. Проверьте почту "
                      "и перейдите по ссылке из письма для подтверждения регистрации."),
    }