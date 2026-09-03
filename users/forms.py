from django.contrib.auth.forms import UserCreationForm
from users.models import User



class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'password1', 'password2']