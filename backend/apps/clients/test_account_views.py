"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-25-account-ledger]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Account/outstanding actions must return a clean 404 when the Account is missing,
not an unhandled DoesNotExist 500."""

import pytest
from django.contrib.auth.models import Group

from apps.clients.models import Account, Client
from apps.users.roles import FIELD_MANAGERS
from apps.users.services import upsert_user_from_claims

pytestmark = pytest.mark.django_db


def _staff_user():
    user = upsert_user_from_claims(
        {
            "sub": "sub-account-404",
            "email": "account404@example.com",
            "given_name": "Account",
            "family_name": "Guard",
        }
    )
    user.groups.add(Group.objects.get(name=FIELD_MANAGERS))
    return user


@pytest.mark.parametrize("suffix", ["account", "outstanding"])
def test_missing_account_returns_404(client, suffix):
    row = Client.objects.create(name="Orphaned account client")
    Account.objects.filter(client=row).delete()
    client.force_login(_staff_user())
    response = client.get(f"/api/clients/{row.pk}/{suffix}/")
    assert response.status_code == 404
