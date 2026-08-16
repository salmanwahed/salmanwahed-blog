import os
from urllib.parse import urljoin

from django.conf import settings
from django.db import models
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _


class ProjectImage(models.Model):
    class ImageType(models.TextChoices):
        HERO = "BANNER", _("Banner")
        THUMBNAIL = "THUMB", _("Thumbnail")
        BASIC = "BASIC", _("Basic")

    name = models.CharField(max_length=40, verbose_name="File Name")
    orig_image = models.ImageField(upload_to="portfolio")
    compressed_image = models.URLField(null=True, blank=True)
    image_type = models.CharField(max_length=10, choices=ImageType.choices, default=ImageType.BASIC)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def image_preview(self):
        return mark_safe(f'<img src="/upload/{self.orig_image}" width="auto" height="80" />')

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.orig_image.name)
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if not self.compressed_image:
            self.compressed_image = urljoin(settings.CDN_URL, self.orig_image.url)
            self.save()
        if settings.USE_CDN:
            return self.compressed_image
        return self.orig_image.url

    def __str__(self):
        return f"{self.name}({self.pk})"


class Tag(models.Model):
    tag_name = models.CharField(max_length=20, unique=True)
    color_code = models.CharField(max_length=8, null=True, blank=True)
    external_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tag_name

    def tag_color(self):
        return mark_safe(f'<img width="15" height="15" style="background-color:{self.color_code};"/>')


class Project(models.Model):
    class ProjectType(models.TextChoices):
        MOBILE_APP = "MOBILE_APP", _("Mobile Application")
        WEB_APP = "WEB_APP", _("")

    class Status(models.TextChoices):
        LIVE = "LIVE", _("Live")
        ONGOING = "ONGOING", _("Ongoing")
        CLOSED = "CLOSED", _("Closed")

    class Category(models.TextChoices):
        PROFESSIONAL = "PROFESSIONAL", _("Professional work")
        PERSONAL = "PERSONAL", _("Personal Works")

    name = models.CharField(max_length=100)
    short_description = models.CharField(max_length=200, blank=True, null=True, verbose_name="Short Description")
    description = models.TextField(null=True, blank=True)
    tag = models.ManyToManyField(Tag, related_name="projects")
    banner = models.ForeignKey(
        ProjectImage, on_delete=models.SET_NULL, null=True, blank=True, related_name="related_projects"
    )
    thumbnail = models.ForeignKey(
        ProjectImage, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects"
    )
    project_url = models.URLField(verbose_name="Project URL", blank=True, null=True)
    project_type = models.CharField(
        max_length=20, choices=ProjectType.choices, default=ProjectType.MOBILE_APP, verbose_name="Project Type"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LIVE)
    # Splits the projects page into its "Professional work" and "Personal
    # Works" sections. Within each, is_featured decides the card shape.
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.PERSONAL, db_index=True)
    # The two halves of the meta badge on a featured card, rendered as
    # "primary · secondary". Deliberately unnamed for content: they hold a job
    # title and dates on one project and a market segment and a tech stack on
    # the next.
    meta_primary = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Meta primary",
        help_text="First half of the badge on a featured card. e.g. FinTech, or Senior Software Engineer",
    )
    meta_secondary = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Meta secondary",
        help_text="Second half, shown after a divider. e.g. Backend & Android, or 2019 — Present",
    )
    is_featured = models.BooleanField(default=False, help_text='Shows the "Featured" badge.')
    project_weight = models.SmallIntegerField(default=0)
    source_url = models.URLField(verbose_name="Source URL", blank=True, null=True)
    utm_url = models.URLField(verbose_name="UTM Url", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def uses_featured_card(self):
        """Whether this project earns the wide card rather than a grid card.

        Either it is flagged, or it has headline stats -- a project with numbers
        worth quoting needs the room to show them, and a grid card has nowhere
        to put them. Reads self.stats.all() rather than .exists() so the view's
        prefetch is used instead of one query per project.
        """
        return self.is_featured or bool(self.stats.all())

    def __str__(self):
        return self.name


class ProjectStat(models.Model):
    """A single headline number on a featured project card, e.g. "8M+ / Users"."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="stats")
    label = models.CharField(max_length=100, help_text="e.g. Users")
    value = models.CharField(max_length=100, help_text="e.g. 8M+")
    order = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.value} {self.label}"


class AppPrivacyPolicy(models.Model):
    name = models.TextField(max_length=255)
    slug = models.TextField(max_length=255, unique=True, db_index=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
