# seller_reports/urls.py
from django.urls import path
from . import views

app_name = "seller_reports"
urlpatterns = [
    path("profit/", views.profit_dashboard, name="profit_dashboard"),
    path("profit/chart-data/", views.profit_chart_data, name="profit_chart_data"),
    path("profit/export-csv/", views.export_profit_csv, name="profit_export_csv"),
]
