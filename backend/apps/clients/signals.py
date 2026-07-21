"""Create the one-to-one Account the moment a Client is created."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.clients.models import Account, Client


@receiver(post_save, sender=Client)
def create_account_for_client(sender, instance, created, **kwargs):
    if created:
        Account.objects.get_or_create(client=instance)
