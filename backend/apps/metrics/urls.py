from django.urls import path

from apps.metrics import views

urlpatterns = [
    path("clients/<int:pk>/metrics/summary/", views.SummaryView.as_view(), name="metrics-summary"),
    path("clients/<int:pk>/metrics/daily-cost/", views.DailyCostView.as_view(), name="metrics-daily-cost"),
    path("clients/<int:pk>/metrics/growth/", views.GrowthView.as_view(), name="metrics-growth"),
    path("clients/<int:pk>/metrics/conversion/", views.ConversionView.as_view(), name="metrics-conversion"),
    path("clients/<int:pk>/metrics/mortality/", views.MortalityView.as_view(), name="metrics-mortality"),
    path("clients/<int:pk>/metrics/account/", views.AccountEvolutionView.as_view(), name="metrics-account"),
]
