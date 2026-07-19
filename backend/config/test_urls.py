"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-02-initial-stack]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.test import Client


def test_admin_is_mounted_and_gated():
    client = Client()
    response = client.get("/admin/")
    assert response.status_code == 302
    assert response["Location"].startswith("/admin/login/")


def test_admin_login_page_serves():
    client = Client()
    response = client.get("/admin/login/")
    assert response.status_code == 200
