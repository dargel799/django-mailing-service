from django import forms
from django.forms import modelformset_factory

from mailings.models import Mailing, Message, Client


class MailingForm(forms.ModelForm):
    subject = forms.CharField(
        max_length=300,
        label='Тема письма',
    )
    body = forms.CharField(
        widget=forms.Textarea,
        label='Текст письма',
    )

    class Meta:
        model = Mailing
        fields = ['first_send_at', 'periodicity', 'clients']
        widgets = {
            'first_send_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'clients': forms.SelectMultiple(attrs={'class': 'd-none', 'id': 'id_clients'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.message_id:
            self.fields['subject'].initial = self.instance.message.subject
            self.fields['body'].initial = self.instance.message.body

    def save(self, commit=True):
        mailing = super().save(commit=False)

        if mailing.pk and mailing.message_id:
            message = mailing.message
            message.subject = self.cleaned_data['subject']
            message.body = self.cleaned_data['body']
        else:
            message = Message(
                subject=self.cleaned_data['subject'],
                body=self.cleaned_data['body'],
            )

        message.save()
        mailing.message = message

        if commit:
            mailing.save()
            self.save_m2m()

        return mailing


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ('full_name', 'email', 'comment')
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

ClientFormSet = modelformset_factory(
    Client,
    fields=('full_name', 'email', 'comment'),
    extra=2,
    can_delete=True
)