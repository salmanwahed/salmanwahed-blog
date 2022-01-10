from django.contrib import admin
from django import forms

from .models import BlogPost, BlogImages, Tag
from ckeditor.widgets import CKEditorWidget


class BlogPostAdminForm(forms.ModelForm):
    body = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = BlogPost
        fields = ['title', 'slug', 'author', 'hero_image', 'tag', 'body', 'status']


class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm


admin.site.register(BlogImages)
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Tag)
