"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

from django.conf import settings
from django.core.checks import Error, register


@register(deploy=True)
def check_auth_hard_guards(app_configs, **kwargs):
    errors = []
    if getattr(settings, "AUTH_DEV_MODE", False):
        errors.append(
            Error(
                "AUTH_DEV_MODE is enabled in a deploy context.",
                hint="Dev login must never run in production; unset AUTH_DEV_MODE.",
                id="users.E001",
            )
        )
    if settings.DEBUG:
        errors.append(
            Error(
                "DEBUG is True in a deploy context.",
                hint="Production must run DEBUG=false (docs/VARIABLES.md); "
                "DEBUG=True wires the dev auth path.",
                id="users.E002",
            )
        )
    return errors
