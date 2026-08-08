from django.urls import path

from .views import AppPrivacyPolicyView, ContactView, ProjectListView, ResumeView

app_name = "portfolio"

# This urlconf is mounted at the site root, not under "portfolio/", so the
# prefix is spelled out on the paths that need it. That keeps the existing
# /portfolio/ URLs byte-identical while letting Resume and Contact live at
# /resume/ and /contact/ under a single "portfolio" namespace.
urlpatterns = [
    path("portfolio/", ProjectListView.as_view(), name="portfolio_view"),
    path("portfolio/app/privacy-policy/<slug:slug>/", AppPrivacyPolicyView.as_view(), name="app_privacy_policy"),
    path("resume/", ResumeView.as_view(), name="resume"),
    path("contact/", ContactView.as_view(), name="contact"),
]
