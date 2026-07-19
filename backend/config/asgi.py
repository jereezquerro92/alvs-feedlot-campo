"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-16-async-mandatory]] · [[adr-02-initial-stack]]
Docs: [[BACKEND]] · [[INFRASTRUCTURE]]
LIVE-DOC:END"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
