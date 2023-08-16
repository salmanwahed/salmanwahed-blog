import logging
from django.views.generic import ListView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .models import Project
from .apps import PortfolioConfig

logger = logging.getLogger('default')


class ProjectListView(ListView):
    model = Project
    ordering = ['-project_weight']
    queryset = Project.objects.select_related('thumbnail', 'banner').prefetch_related('tag')

    @method_decorator(cache_page(timeout=45*60, key_prefix=PortfolioConfig.name))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
