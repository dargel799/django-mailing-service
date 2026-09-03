from django import forms

from mailings.models import Mailing


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['first_send_at', 'periodicity', 'clients']