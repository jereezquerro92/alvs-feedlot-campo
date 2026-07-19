"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import logging

from django.conf import settings
from django.contrib.auth.models import Group

from apps.users.models import AccessRequest, User

logger = logging.getLogger(__name__)

IDENTITY_CLAIMS = ("email", "given_name", "family_name", "picture")


def _apply_bootstrap_allowlist(user, access_request):
    # adr-21: fills role only while null (the admin stays authoritative);
    # a pair naming a missing Group is skipped — a config typo must never
    # break login or mint a new Group.
    if access_request.role_id is not None or not user.email:
        return
    group_name = settings.AUTH_BOOTSTRAP_ALLOWLIST.get(user.email.lower())
    if not group_name:
        return
    group = Group.objects.filter(name=group_name).first()
    if group is None:
        logger.warning(
            "AUTH_BOOTSTRAP_ALLOWLIST names unknown group %r for %s; grant skipped",
            group_name,
            user.email,
        )
        return
    access_request.role = group
    access_request.save()


def upsert_user_from_claims(claims):
    sub = claims["sub"]
    mirror = {name: claims.get(name, "") for name in IDENTITY_CLAIMS}
    user, created = User.objects.get_or_create(sub=sub, defaults=mirror)
    if not created:
        changed = False
        for name in IDENTITY_CLAIMS:
            if name in claims and getattr(user, name) != claims[name]:
                setattr(user, name, claims[name])
                changed = True
        if changed:
            user.save()
    access_request, _ = AccessRequest.objects.get_or_create(user=user)
    _apply_bootstrap_allowlist(user, access_request)
    return user
