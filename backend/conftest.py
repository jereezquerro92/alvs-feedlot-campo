import pytest
from django.core.management import call_command


@pytest.fixture(scope="session", autouse=True)
def _collectstatic():
    """Build the WhiteNoise manifest once per test session.

    Mirrors the `collectstatic --noinput` build step in backend/Dockerfile:
    without it, CompressedManifestStaticFilesStorage.url() raises for any
    template using {% static %} (e.g. the Django admin login page).
    """
    call_command("collectstatic", interactive=False, verbosity=0)
