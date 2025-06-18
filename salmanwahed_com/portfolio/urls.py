from django.urls import path
from .views import ProjectListView, AppPrivacyPolicyView

app_name = 'portfolio'

urlpatterns = [
    path('', ProjectListView.as_view(), name="portfolio_view"),
    path('app/privacy-policy/<slug:slug>/', AppPrivacyPolicyView.as_view(), name='app_privacy_policy'),
]