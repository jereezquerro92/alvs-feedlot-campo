"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

import re

from rest_framework import serializers

from apps.users.models import User

READ_ONLY_FIELDS = ["sub", "email", "given_name", "family_name", "picture", "groups"]

THEME_TOP_LEVEL_KEYS = {"mode", "bgPreset", "colors", "radius"}
THEME_COLOR_KEYS = {"background", "primary", "secondary", "accent"}
THEME_MODE_CHOICES = {"light", "dark"}
THEME_BG_PRESET_CHOICES = {"default", "melt"}

_COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{3,8}|rgb(a)?\(.*\)|hsl\(.*\)|oklch\(.*\))$")
_COLOR_FORBIDDEN_CHARS = frozenset(";{}<>\"'")
_COLOR_FORBIDDEN_SUBSTRINGS = ("url", "expression")

# Mirrors frontend/src/lib/theme.ts's RADIUS_PATTERN exactly — the server is
# the boundary, not the frontend's re-sanitization ([[GLOSSARY]]: theme_config).
_RADIUS_RE = re.compile(r"^[0-9]*\.?[0-9]+(px|rem|em|%|vh|vw|ch)$")


def _is_valid_color(value):
    if not isinstance(value, str) or not _COLOR_RE.match(value):
        return False
    if any(char in value for char in _COLOR_FORBIDDEN_CHARS):
        return False
    lowered = value.lower()
    return not any(substring in lowered for substring in _COLOR_FORBIDDEN_SUBSTRINGS)


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = User
        fields = READ_ONLY_FIELDS + ["nickname", "avatar_visible", "theme_config"]
        read_only_fields = ["sub", "email", "given_name", "family_name", "picture"]

    def validate_theme_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("theme_config must be an object.")
        unknown = set(value) - THEME_TOP_LEVEL_KEYS
        if unknown:
            raise serializers.ValidationError(f"Unknown theme_config key(s): {sorted(unknown)}.")
        if "mode" in value and value["mode"] not in THEME_MODE_CHOICES:
            raise serializers.ValidationError("mode must be one of: light, dark.")
        if "bgPreset" in value and value["bgPreset"] not in THEME_BG_PRESET_CHOICES:
            raise serializers.ValidationError("bgPreset must be one of: default, melt.")
        if "colors" in value:
            colors = value["colors"]
            if not isinstance(colors, dict):
                raise serializers.ValidationError("colors must be an object.")
            unknown_colors = set(colors) - THEME_COLOR_KEYS
            if unknown_colors:
                raise serializers.ValidationError(f"Unknown colors key(s): {sorted(unknown_colors)}.")
            for key, color in colors.items():
                if not _is_valid_color(color):
                    raise serializers.ValidationError(f"colors.{key} is not a valid color value.")
        if "radius" in value:
            radius = value["radius"]
            if not isinstance(radius, str) or not _RADIUS_RE.match(radius):
                raise serializers.ValidationError("radius must be a valid CSS length (px/rem/em/%/vh/vw/ch).")
        return value

    def validate(self, attrs):
        if self.instance is not None:
            for name in ("email", "given_name", "family_name", "picture"):
                if name in self.initial_data and self.initial_data[name] != getattr(self.instance, name):
                    raise serializers.ValidationError({name: "This field is read-only."})
            if "groups" in self.initial_data:
                current = list(self.instance.groups.values_list("name", flat=True))
                if self.initial_data["groups"] != current:
                    raise serializers.ValidationError({"groups": "This field is read-only."})
            if "sub" in self.initial_data and self.initial_data["sub"] != self.instance.sub:
                raise serializers.ValidationError({"sub": "This field is read-only."})
        return attrs
