import logging
from django.views.generic import ListView

from .models import Project

logger = logging.getLogger('default')


class ProjectListView(ListView):
    model = Project
    ordering = ['-project_weight']

    def get(self, request, *args, **kwargs):
        logger.info('Creating Portfolio View')
        return super(ProjectListView, self).get(request, *args, **kwargs)
