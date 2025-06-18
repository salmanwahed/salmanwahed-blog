import logging
from django.views.generic import ListView, DetailView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .models import Project, AppPrivacyPolicy
from .apps import PortfolioConfig

logger = logging.getLogger('default')


class ProjectListView(ListView):
    model = Project
    ordering = ['-project_weight']
    queryset = Project.objects.select_related('thumbnail', 'banner').prefetch_related('tag')

    @method_decorator(cache_page(timeout=45*60, key_prefix=PortfolioConfig.name))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class AppPrivacyPolicyView(DetailView):
    model = AppPrivacyPolicy
    template_name = 'portfolio/app_privacy_policy.html'
    context_object_name = 'policy'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'