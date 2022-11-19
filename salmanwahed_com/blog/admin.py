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
        fields = ['title', 'slug', 'tag', 'body', 'author', 'hero_image', 'thumbnail', 'short_desc', 'status']


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'publish_date', 'visited_count', 'blog_preview')
    form = BlogPostAdminForm

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.title)
        if obj.status == BlogPost.Status.PUBLISHED and obj.publish_date is None:
            obj.publish_date = timezone.now()
        if getattr(obj, 'author', None) is None:
            obj.author = request.user
        super(BlogPostAdmin, self).save_model(request, obj, form, change)


class BlogImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_url', 'image_type', 'image_preview')
    readonly_fields = ('image_preview',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('tag_name', 'tag_name_bn', 'color_code', 'tag_color')
    readonly_fields = ('tag_color',)


admin.site.register(BlogImages, BlogImageAdmin)
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Tag, TagAdmin)
