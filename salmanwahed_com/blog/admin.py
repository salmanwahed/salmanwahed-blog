from django.contrib import admin
from django import forms
from django.utils.text import slugify
from django.utils import timezone

from .models import BlogPost, BlogImages, Tag
from ckeditor.widgets import CKEditorWidget


class BlogPostAdminForm(forms.ModelForm):
    body = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = BlogPost
        fields = ['title', 'slug', 'author', 'hero_image', 'thumbnail', 'tag', 'short_desc', 'body', 'status']


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'publish_date', 'visited_count')
    form = BlogPostAdminForm

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.title)
        if obj.status == BlogPost.Status.PUBLISHED:
            obj.publish_date = timezone.now()
        if getattr(obj, 'author', None) is None:
            obj.author = request.user
        super(BlogPostAdmin, self).save_model(request, obj, form, change)


admin.site.register(BlogImages)
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Tag)
