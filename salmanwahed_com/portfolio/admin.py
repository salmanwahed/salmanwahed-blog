from django import forms
from django.contrib import admin

from .models import AppPrivacyPolicy, Project, ProjectImage, ProjectStat, Tag


class ProjectStatInline(admin.TabularInline):
    """The three headline numbers on a featured professional card."""

    model = ProjectStat
    extra = 3
    fields = ("value", "label", "order")


class ProjectAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "category",
            "short_description",
            "description",
            "role",
            "period",
            "is_featured",
            "tag",
            "thumbnail",
            "banner",
            "project_url",
            "utm_url",
            "source_url",
            "project_type",
            "status",
            "project_weight",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6, "cols": 90}),
            "short_description": forms.Textarea(attrs={"rows": 2, "cols": 90}),
        }


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_featured", "project_type", "status", "project_weight")
    list_filter = ("category", "is_featured", "project_type", "status")
    form = ProjectAdminForm
    inlines = [ProjectStatInline]


class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ("name", "image_url", "image_type", "image_preview")
    readonly_fields = ("image_preview",)


class TagAdmin(admin.ModelAdmin):
    list_display = ("tag_name", "external_url", "color_code", "tag_color")
    readonly_fields = ("tag_color",)


class AppPrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
    )


admin.site.register(ProjectImage, ProjectImageAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(AppPrivacyPolicy, AppPrivacyPolicyAdmin)
