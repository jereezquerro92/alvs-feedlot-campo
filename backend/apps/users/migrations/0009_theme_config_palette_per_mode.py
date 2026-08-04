# LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
# Governed by: [[adr-10-auth]] · [[adr-51-api-and-backend]]
# Docs: [[BACKEND]] · [[AUTH]]
# LIVE-DOC:END

from django.db import migrations

LEGACY_TO_CURRENT = {"background": "surface"}
COLOR_KEYS = {"canvas", "dots", "surface", "foreground", "primary", "secondary", "accent"}
MODES = ("light", "dark")


def _is_flat(colors):
    """A pre-per-mode palette: a colors map with no mode key in it."""
    return isinstance(colors, dict) and colors and not any(mode in colors for mode in MODES)


def to_per_mode(apps, schema_editor):
    """A flat palette becomes the palette of the mode the same blob declares.

    That mode is the only mode the colors were ever tuned against — the editor
    showed one mode at a time — so nesting them under it preserves what the
    user actually saw, and leaves the other mode unset for them to fill in.
    """
    User = apps.get_model("users", "User")

    for user in User.objects.exclude(theme_config={}).iterator():
        config = user.theme_config
        if not isinstance(config, dict) or not _is_flat(config.get("colors")):
            continue

        palette = {
            LEGACY_TO_CURRENT.get(key, key): value
            for key, value in config["colors"].items()
            if LEGACY_TO_CURRENT.get(key, key) in COLOR_KEYS
        }

        config["colors"] = {config.get("mode", "dark"): palette} if palette else {}
        user.theme_config = config
        user.save(update_fields=["theme_config"])


def to_flat(apps, schema_editor):
    """Collapse back to one palette, keeping the declared mode's."""
    User = apps.get_model("users", "User")
    current_to_legacy = {v: k for k, v in LEGACY_TO_CURRENT.items()}

    for user in User.objects.exclude(theme_config={}).iterator():
        config = user.theme_config
        colors = config.get("colors") if isinstance(config, dict) else None
        if not isinstance(colors, dict) or _is_flat(colors):
            continue

        palette = colors.get(config.get("mode", "dark")) or next(
            (p for p in colors.values() if p), {}
        )
        config["colors"] = {
            current_to_legacy.get(key, key): value
            for key, value in palette.items()
            if current_to_legacy.get(key, key) in {"background", "primary", "secondary", "accent"}
        }
        user.theme_config = config
        user.save(update_fields=["theme_config"])


class Migration(migrations.Migration):
    dependencies = [("users", "0008_accessrequest_client")]

    operations = [migrations.RunPython(to_per_mode, to_flat)]
