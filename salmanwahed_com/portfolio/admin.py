from django.contrib import admin

from .models import ProjectImage, Project, Tag
from django import forms
from ckeditor.widgets import CKEditorWidget


class ProjectAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget(), required=False)

    class Meta:
        model = Project
        fields = ['name', 'short_description', 'tag', 'thumbnail', 'project_url', 'utm_url', 'source_url',
                  'project_type', 'status', 'project_weight']


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_type', 'status')
    form = ProjectAdminForm


class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_url', 'image_type', 'image_preview')
    readonly_fields = ('image_preview',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('tag_name', 'external_url', 'color_code', 'tag_color')
    readonly_fields = ('tag_color',)


admin.site.register(ProjectImage, ProjectImageAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Tag, TagAdmin)
