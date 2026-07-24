"""Seed the four price sources so the ingest command has something to iterate."""

from django.db import migrations


def seed(apps, schema_editor):
    MarketSource = apps.get_model("market", "MarketSource")
    rows = [
        # slug, name, kind, is_automated, notes
        ("canuelas", "Mercado Agroganadero (Cañuelas)", "market", True,
         "Fuente primaria diaria por categoría. Scraper cp1252, rezago de un día."),
        ("ipcva", "IPCVA — Precios en Pie", "index", True,
         "Segunda fuente automática (mensual). Endpoint AJAX pendiente de cablear."),
        ("rosgan", "ROSGAN — Índice", "index", False,
         "Complementaria. Sitio JS-rendered: carga manual por ahora."),
        ("manual", "Carga manual", "market", False,
         "Respaldo siempre disponible. Sin conector."),
    ]
    for slug, name, kind, automated, notes in rows:
        MarketSource.objects.update_or_create(
            slug=slug,
            defaults={"name": name, "kind": kind, "is_automated": automated, "notes": notes},
        )


def unseed(apps, schema_editor):
    MarketSource = apps.get_model("market", "MarketSource")
    MarketSource.objects.filter(slug__in=["canuelas", "ipcva", "rosgan", "manual"]).delete()


class Migration(migrations.Migration):
    dependencies = [("market", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
