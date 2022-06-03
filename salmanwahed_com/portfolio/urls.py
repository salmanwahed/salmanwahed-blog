from django.urls import path
from .views import ProjectListView

app_name = 'portfolio'

urlpatterns = [
    path('', ProjectListView.as_view(), name="portfolio_view"),
]