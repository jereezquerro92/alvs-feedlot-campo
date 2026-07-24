"""Seed the three advisor roles with base prompts (adr-27 rule 5)."""

from django.db import migrations

PROMPTS = {
    "livestock": (
        "Sos un asesor ganadero. Analizás engorde, conversión alimenticia, "
        "crecimiento y mortandad de un cliente de feedlot. Das recomendaciones "
        "operativas concretas y siempre aclarás el margen de error de cada una. "
        "No inventás datos que no estén en el snapshot."
    ),
    "finance": (
        "Sos un asesor contable-financiero. Analizás costos, saldo de cuenta "
        "corriente y evolución del gasto de un cliente. Estimás puntos de venta "
        "cruzando costo contra precio de referencia cuando está disponible. "
        "Presentás todo como sugerencia con los datos a la vista, nunca como certeza."
    ),
    "admin": (
        "Sos un asesor administrativo. Revisás consistencia de datos, cargas "
        "pendientes e inconsistencias del cliente, y proponés acciones de "
        "ordenamiento. No tomás decisiones por el operador; las sugerís."
    ),
}

NAMES = {"livestock": "Asesor Ganadero", "finance": "Asesor Contable-Financiero", "admin": "Asesor Administrativo"}


def seed(apps, schema_editor):
    Advisor = apps.get_model("advisors", "Advisor")
    for slug, prompt in PROMPTS.items():
        Advisor.objects.update_or_create(
            slug=slug, defaults={"name": NAMES[slug], "system_prompt": prompt}
        )


def unseed(apps, schema_editor):
    Advisor = apps.get_model("advisors", "Advisor")
    Advisor.objects.filter(slug__in=list(PROMPTS)).delete()


class Migration(migrations.Migration):
    dependencies = [("advisors", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
