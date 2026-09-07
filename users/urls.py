from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from users.apps import UsersConfig
from users.forms import EmailAuthenticationForm
from users.views import RegisterView, confirm_email


app_name = UsersConfig.name

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(template_name='users/login.html', authentication_form=EmailAuthenticationForm), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('confirm-email/<str:token>', confirm_email, name='confirm_email')
]