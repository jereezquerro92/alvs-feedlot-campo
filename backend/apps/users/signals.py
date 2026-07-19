"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import AccessRequest


@receiver(post_save, sender=AccessRequest)
def add_role_group_membership(sender, instance, **kwargs):
    if instance.role_id is not None:
        instance.user.groups.add(instance.role)
