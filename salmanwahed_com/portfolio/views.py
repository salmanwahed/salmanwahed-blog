from django.shortcuts import render
from django.views.generic import ListView
from .models import Project


class ProjectListView(ListView):
    model = Project
