from django import forms
from django.forms import modelformset_factory

from mailings.models import Mailing, Message, Client
from mailings.services import compute_next_send_at


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
        fields = ['first_send_at', 'periodicity', 'clients', 'end_send_at']
        widgets = {
            'first_send_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'clients': forms.SelectMultiple(attrs={'class': 'd-none', 'id': 'id_clients'}),
            'end_send_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.message_id:
            self.fields['subject'].initial = self.instance.message.subject
            self.fields['body'].initial = self.instance.message.body

    def clean(self):
        cleaned_data = super().clean()
        first_send_at = cleaned_data.get('first_send_at')
        end_send_at = cleaned_data.get('end_send_at')

        if first_send_at and end_send_at and end_send_at <= first_send_at:
            self.add_error(
                'end_send_at',
                'Дата последней отправки должна быть позже даты первой отправки.'
            )

        return cleaned_data

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
        mailing.next_send_at = compute_next_send_at(mailing.first_send_at, mailing.periodicity)

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