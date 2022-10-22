import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from django.conf import settings
from urllib.parse import urljoin


class ProjectImage(models.Model):
    class ImageType(models.TextChoices):
        HERO = 'BANNER', _('Banner')
        THUMBNAIL = 'THUMB', _('Thumbnail')
        BASIC = 'BASIC', _('Basic')

    name = models.CharField(max_length=40, verbose_name='File Name')
    orig_image = models.ImageField(upload_to='portfolio')
    compressed_image = models.URLField(null=True, blank=True)
    image_type = models.CharField(max_length=10, choices=ImageType.choices, default=ImageType.BASIC)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def image_preview(self):
        return mark_safe('<img src="/upload/%s" width="auto" height="80" />' % self.orig_image)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.orig_image.name)
        super(ProjectImage, self).save(*args, **kwargs)

    @property
    def image_url(self):
        if not self.compressed_image:
            self.compressed_image = urljoin(settings.CDN_URL, self.orig_image.url)
            self.save()
        if settings.USE_CDN:
            return self.compressed_image
        return self.orig_image.url

    def __str__(self):
        return '{}({})'.format(self.name, self.pk)


class Tag(models.Model):
    tag_name = models.CharField(max_length=20, unique=True)
    color_code = models.CharField(max_length=8, null=True, blank=True)
    external_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tag_name

    def tag_color(self):
        return mark_safe('<img width="15" height="15" style="background-color:%s;"/>' % self.color_code)


class Project(models.Model):
    class ProjectType(models.TextChoices):
        MOBILE_APP = 'MOBILE_APP', _('Mobile Application')
        WEB_APP = 'WEB_APP', _('')

    class Status(models.TextChoices):
        LIVE = 'LIVE', _('Live')
        ONGOING = 'ONGOING', _('Ongoing')
        CLOSED = 'CLOSED', _('Closed')

    name = models.CharField(max_length=100)
    short_description = models.CharField(max_length=200, blank=True, null=True, verbose_name='Short Description')
    description = models.TextField(null=True, blank=True)
    tag = models.ManyToManyField(Tag)
    banner = models.ForeignKey(ProjectImage, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="banner")
    thumbnail = models.ForeignKey(ProjectImage, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="thumbnail")
    project_url = models.URLField(verbose_name="Project URL", blank=True, null=True)
    project_type = models.CharField(max_length=20, choices=ProjectType.choices, default=ProjectType.MOBILE_APP,
                                    verbose_name='Project Type')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LIVE)
    project_weight = models.SmallIntegerField(default=0)
    source_url = models.URLField(verbose_name="Source URL", blank=True, null=True)
    utm_url = models.URLField(verbose_name='UTM Url', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
