from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.text import slugify

from .models import BlogImages, BlogPost, Tag


class BlogPostAdminForm(forms.ModelForm):
    """Post form. The body textarea is upgraded to EasyMDE by admin-editor.js.

    Keeping it a plain <textarea> in the markup means the form still works with
    JavaScript off, and a legacy HTML post can be edited as raw HTML without a
    rich-text editor silently reformatting it.
    """

    class Meta:
        model = BlogPost
        fields = [
            "title",
            "slug",
            "tag",
            "body_format",
            "body",
            "author",
            "hero_image",
            "thumbnail",
            "short_desc",
            "status",
        ]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 30, "class": "markdown-editor"}),
            "short_desc": forms.Textarea(attrs={"rows": 3}),
        }

    class Media:
        css = {"all": ("vendor/easymde.min.css", "css/admin-editor.css")}
        js = ("vendor/easymde.min.js", "js/admin-editor.js")


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "body_format", "publish_date", "visited_count", "blog_preview")
    list_filter = ("status", "body_format")
    form = BlogPostAdminForm

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.title)
        if obj.status == BlogPost.Status.PUBLISHED and obj.publish_date is None:
            obj.publish_date = timezone.now()
        if getattr(obj, "author", None) is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class BlogImageAdmin(admin.ModelAdmin):
    list_display = ("name", "image_url", "image_type", "image_preview")
    readonly_fields = ("image_preview",)


class TagAdmin(admin.ModelAdmin):
    list_display = ("tag_name", "tag_name_bn", "color_code", "tag_color")
    readonly_fields = ("tag_color",)


admin.site.register(BlogImages, BlogImageAdmin)
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Tag, TagAdmin)
