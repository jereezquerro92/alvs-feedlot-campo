"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.permissions import BasePermission

ADMINS_GROUP = "admins"


class HasAnyGroup(BasePermission):
    """Base permission: authenticated user must belong to at least one of
    `group_names`. Subclasses set `group_names`; the check *shape* is shared,
    the group set is not ([[adr-10-auth]] rule 2)."""

    group_names = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated) and user.groups.filter(
            name__in=self.group_names
        ).exists()


class IsInAdminsGroup(HasAnyGroup):
    group_names = (ADMINS_GROUP,)
