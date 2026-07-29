"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from django.urls import path

from apps.metrics import views

urlpatterns = [
    path("clients/<int:pk>/metrics/summary/", views.SummaryView.as_view(), name="metrics-summary"),
    path("clients/<int:pk>/metrics/daily-cost/", views.DailyCostView.as_view(), name="metrics-daily-cost"),
    path("clients/<int:pk>/metrics/growth/", views.GrowthView.as_view(), name="metrics-growth"),
    path("clients/<int:pk>/metrics/conversion/", views.ConversionView.as_view(), name="metrics-conversion"),
    path("clients/<int:pk>/metrics/mortality/", views.MortalityView.as_view(), name="metrics-mortality"),
    path("clients/<int:pk>/metrics/account/", views.AccountEvolutionView.as_view(), name="metrics-account"),
    path("clients/<int:pk>/metrics/gross-margin/", views.GrossMarginView.as_view(), name="metrics-gross-margin"),
    path("clients/<int:pk>/metrics/reproduction/", views.ReproductionView.as_view(), name="metrics-reproduction"),
    path("semen-stock/", views.SemenStockView.as_view(), name="metrics-semen-stock"),
]
