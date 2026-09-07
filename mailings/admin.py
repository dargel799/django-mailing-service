from django.contrib import admin

from mailings.models import Message, Mailing, Client


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'body']
    search_fields = ['subject']

@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_send_at', 'periodicity', 'status', 'message', 'get_clients']
    list_display_links = ['message', 'status']
    list_filter = ['status', 'periodicity']
    search_fields = ['message__subject']
    ordering = ['-first_send_at']
    filter_horizontal = ['clients']

    @admin.display(description='Клиенты')
    def get_clients(self, obj):
        return ', '.join(client.email for client in obj.clients.all())


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name']
    search_fields = ['email']
