# DRF + ORM patterns (kdx-django-6-drf)

Load only when implementing models, serializers, viewsets, or HTMX fragments. English identifiers; prefer no comments in real source (snippets here are instructional).

## Model skeleton

```python
from django.db import models
from django.db.models import Q


class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="%(app_label)s_%(class)s_price_gte_0",
            ),
        ]

    def __str__(self) -> str:
        return self.name
```

- Prefer `BigAutoField` default PK unless non-enumerable public IDs are required → then `UUIDField(default=uuid.uuid4, editable=False, unique=True)` (or PK).
- Index what you filter/order on; do not index everything.

## QuerySet / manager

```python
class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def with_relations(self):
        return self.select_related("category").prefetch_related("tags")


class Product(models.Model):
    objects = ProductQuerySet.as_manager()
```

## Serializers (split by action)

```python
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "slug", "price", "is_active", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "price", "is_active"]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be non-negative.")
        return value


class ProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "price", "is_active"]
```

Never `fields = "__all__"`. Heavy create/update logic → service module, not serializer.

## ViewSet

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema_view, extend_schema


@extend_schema_view(
    list=extend_schema(tags=["Product"]),
    retrieve=extend_schema(tags=["Product"]),
    create=extend_schema(tags=["Product"]),
)
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()
        return Product.objects.with_relations()

    def get_serializer_class(self):
        if self.action == "create":
            return ProductCreateSerializer
        if self.action in ("update", "partial_update"):
            return ProductUpdateSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
```

## Router / trailing slash

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()  # trailing slash ON
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path("api/", include(router.urls)),
]
```

## Permissions (object)

```python
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "created_by_id", None) == request.user.id
```

## Settings fragments (env-driven)

```python
# DATABASE — always Postgres; URL from env
# CACHE — DatabaseCache default; LocMemCache optional alias
# STORAGES — modern dict only
# SECURE_* + SECURE_CSP in production when HTTPS terminates at the ALB
```

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "OPTIONS": {"MAX_ENTRIES": 10000, "CULL_FREQUENCY": 3},
        "TIMEOUT": 300,
    },
    "local": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "process-local",
        "TIMEOUT": 60,
    },
}
```

Run `createcachetable` in deploy/setup.

## Background work (Django 6)

```python
from django.tasks import task


@task
def send_receipt(order_id: int) -> None:
    ...
```

Enqueue with the configured backend; workers are infra — not Celery-by-default.

## HTMX fragments (Django produces HTML)

Declare the path in `docs/API.md` first (`Serializer: —`, description says HTML fragment). Prefer a dedicated view over overloading a JSON viewset.

```python
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.views import View


class ProductListFragmentView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        products = Product.objects.active().with_relations()
        return TemplateResponse(
            request,
            "catalog/fragments/product_list.html",
            {"products": products},
        )
```

Partial template (stable root id for `hx-target`):

```html
<div id="product-list">
  {% for product in products %}
    <article data-product-id="{{ product.pk }}">{{ product.name }}</article>
  {% empty %}
    <p>No products.</p>
  {% endfor %}
</div>
```

Mutating fragment (sketch): session auth + CSRF on the form; return the updated region as HTML; optional `response["HX-Trigger"] = "productsUpdated"`.

Detect shared full-page vs fragment only when the contract truly shares one view:

```python
if request.headers.get("HX-Request") == "true":
    return TemplateResponse(request, "…/fragment.html", context)
```

Prefer **separate fragment URLs** when JSON and HTML diverge. Tests: client get/post with `HTTP_HX_REQUEST=true`, assert `text/html` and a key id/string in content.

## pytest sketch

```python
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_list_products_public(api_client: APIClient):
    response = api_client.get("/api/products/")
    assert response.status_code == 200
```

Use `uv run pytest`. Prefer factories over huge fixtures.
