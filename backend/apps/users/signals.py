"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from apps.users.models import AccessRequest, User
from apps.users.permissions import ADMINS_GROUP


@receiver(post_save, sender=AccessRequest)
def add_role_group_membership(sender, instance, **kwargs):
    if instance.role_id is not None:
        instance.user.groups.add(instance.role)


@receiver(m2m_changed, sender=User.groups.through)
def sync_staff_flags_with_admins_group(sender, instance, action, **kwargs):
    # adr-20/adr-21: Group membership is the sole authority; this only mirrors
    # membership in the `admins` group into the two flags Django's admin site
    # requires (is_staff to log in, is_superuser to see every model — `admins`
    # is already the standing app-wide superset, roles.py/GroupMatrixPermission).
    # No email is ever named here — it reacts to Group membership only,
    # however that membership was granted (signal, allowlist, or /admin/ edit).
    if action not in ("post_add", "post_remove", "post_clear"):
        return
    is_admin = instance.groups.filter(name=ADMINS_GROUP).exists()
    if instance.is_staff != is_admin or instance.is_superuser != is_admin:
        instance.is_staff = is_admin
        instance.is_superuser = is_admin
        instance.save(update_fields=["is_staff", "is_superuser"])
