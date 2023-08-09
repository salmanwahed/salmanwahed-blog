import os.path

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from django.conf import settings
from urllib.parse import urljoin


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='anonymous', first_name='Anonymous', last_name='User')[0]


class BlogImages(models.Model):
    class ImageType(models.TextChoices):
        HERO = 'HERO', _('Hero')
        THUMBNAIL = 'THUMB', _('Thumbnail')
        BASIC = 'BASIC', _('Basic')

    name = models.CharField(max_length=255, verbose_name='File Name')
    orig_image = models.ImageField(upload_to='blog')
    compressed_image = models.URLField(null=True, blank=True)
    image_type = models.CharField(max_length=10, choices=ImageType.choices, default=ImageType.BASIC)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=80, null=True, blank=True)

    def image_preview(self):
        return mark_safe('<img src="/upload/%s" width="auto" height="80" />' % self.orig_image)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.orig_image.name)
        super(BlogImages, self).save(*args, **kwargs)

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
    tag_name = models.CharField(max_length=255, unique=True)
    tag_name_bn = models.CharField(max_length=255, null=True, blank=True)
    color_code = models.CharField(max_length=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=80, null=True, blank=True)

    def tag_color(self):
        return mark_safe('<img width="15" height="15" style="background-color:%s;"/>' % self.color_code)

    def __str__(self):
        return self.tag_name


class BlogPost(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0
        PUBLISHED = 1

    title = models.CharField(max_length=255, null=False)
    author = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user), blank=True)
    hero_image = models.ForeignKey(BlogImages, on_delete=models.SET_NULL, null=True, blank=True, related_name="hero")
    thumbnail = models.ForeignKey(BlogImages, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="thumbnail")
    body = models.TextField()
    short_desc = models.TextField(null=True, blank=True, verbose_name="Short Description")
    slug = models.SlugField(max_length=255, allow_unicode=True, unique=True, blank=True)
    tag = models.ManyToManyField(Tag)
    status = models.IntegerField(choices=Status.choices, default=Status.DRAFT)
    publish_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=80, null=True, blank=True)
    visited_count = models.IntegerField(default=0)
    claps_count = models.IntegerField(default=0)
    minutes_to_read = models.IntegerField(default=0)
    remarks = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == BlogPost.Status.PUBLISHED and self.publish_date is None:
            self.publish_date = timezone.now()
        super(BlogPost, self).save(*args, **kwargs)

    def blog_preview(self):
        if self.status == BlogPost.Status.DRAFT:
            return mark_safe('<a href="/post/preview/%s">Preview</a>' % self.id)

    def __str__(self):
        return self.title
