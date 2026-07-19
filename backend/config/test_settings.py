"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-02-initial-stack]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

import subprocess
import sys
from pathlib import Path

from django.conf import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent

_BASE_ENV = {
    "PATH": "/usr/bin:/bin",
    "DJANGO_SETTINGS_MODULE": "config.settings",
}


def _import_settings(env_overrides, expression):
    env = dict(_BASE_ENV)
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", f"import config.settings as s; print({expression})"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


def test_cors_allow_credentials_is_structurally_true():
    assert settings.CORS_ALLOW_CREDENTIALS is True


def test_missing_secret_key_hard_fails_when_not_debug():
    result = _import_settings({"DEBUG": "false"}, "s.SECRET_KEY")
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
    assert "SECRET_KEY" in result.stderr


def test_missing_secret_key_falls_back_only_under_debug():
    result = _import_settings({"DEBUG": "true"}, "s.SECRET_KEY")
    assert result.returncode == 0
    assert "insecure" in result.stdout


def test_explicit_secret_key_boots_without_debug():
    result = _import_settings(
        {"DEBUG": "false", "SECRET_KEY": "prod-key"}, "s.SECRET_KEY"
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "prod-key"


def test_proxy_ssl_header_absent_by_default():
    result = _import_settings(
        {"DEBUG": "true"}, "getattr(s, 'SECURE_PROXY_SSL_HEADER', None)"
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "None"


def test_use_x_forwarded_proto_sets_proxy_ssl_header():
    result = _import_settings(
        {"DEBUG": "false", "SECRET_KEY": "k", "USE_X_FORWARDED_PROTO": "true"},
        "s.SECURE_PROXY_SSL_HEADER",
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "('HTTP_X_FORWARDED_PROTO', 'https')"


def test_secure_cookies_and_hsts_absent_under_debug():
    result = _import_settings(
        {"DEBUG": "true"},
        "(s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, "
        "getattr(s, 'SECURE_HSTS_SECONDS', 0))",
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "(False, False, 0)"


def test_secure_cookies_and_hsts_enabled_without_debug():
    result = _import_settings(
        {"DEBUG": "false", "SECRET_KEY": "prod-key"},
        "(s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, "
        "s.SECURE_HSTS_SECONDS, s.SECURE_HSTS_INCLUDE_SUBDOMAINS)",
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "(True, True, 3600, False)"
