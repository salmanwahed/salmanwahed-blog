import logging
from django.views.generic import ListView

from .models import Project

logger = logging.getLogger('default')


class ProjectListView(ListView):
    model = Project
    ordering = ['-project_weight']
    queryset = Project.objects.select_related('thumbnail', 'banner').prefetch_related('tag')
