
import fnmatch
from pathlib import Path, PurePosixPath

DOCKERIGNORE_PATH = Path(__file__).resolve().parent / ".dockerignore"


def _load_patterns() -> list[str]:
    lines = DOCKERIGNORE_PATH.read_text().splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def _pattern_matches(pattern: str, path: str) -> bool:
    pattern = pattern.rstrip("/")
    if "/" in pattern:
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, f"{pattern}/*")
    parts = PurePosixPath(path).parts
    return any(fnmatch.fnmatch(part, pattern) for part in parts)


def _is_excluded(path: str, patterns: list[str]) -> bool:
    return any(_pattern_matches(pattern, path) for pattern in patterns)


def test_dockerignore_file_exists():
    assert DOCKERIGNORE_PATH.is_file(), "backend/.dockerignore must exist"


EXCLUDED_SAMPLE_PATHS = [
    ".venv/lib/python3.14/site-packages/django/__init__.py",
    ".env",
    ".env.production",
    "__pycache__/apps/health/views.cpython-314.pyc",
    "apps/health/__pycache__/views.cpython-314.pyc",
    ".pytest_cache/v/cache/nodeids",
    ".mypy_cache/3.14/apps/health/views.data.json",
    ".ruff_cache/0.1.0/cache",
    "staticfiles/admin/css/base.css",
]


def test_excludes_host_venv_env_and_caches():
    patterns = _load_patterns()
    still_included = [p for p in EXCLUDED_SAMPLE_PATHS if not _is_excluded(p, patterns)]
    assert not still_included, f"these paths must be excluded from the build image: {still_included}"


KEPT_SAMPLE_PATHS = [
    "manage.py",
    "apps/health/views.py",
    "apps/users/models.py",
    "config/settings.py",
    "pyproject.toml",
    "uv.lock",
]


def test_keeps_application_source():
    patterns = _load_patterns()
    wrongly_excluded = [p for p in KEPT_SAMPLE_PATHS if _is_excluded(p, patterns)]
    assert not wrongly_excluded, f"these paths must NOT be excluded from the build image: {wrongly_excluded}"
