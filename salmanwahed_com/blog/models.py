import os.path

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='anonymous', first_name='Anonymous', last_name='User')[0]


class BlogImages(models.Model):
    class ImageType(models.TextChoices):
        HERO = 'HERO', _('Hero')
        THUMBNAIL = 'THUMB', _('Thumbnail')
        BASIC = 'BASIC', _('Basic')

    name = models.CharField(max_length=40, verbose_name='File Name')
    orig_image = models.ImageField(upload_to='images')
    compressed_image = models.URLField(null=True, blank=True)
    image_type = models.CharField(max_length=10, choices=ImageType.choices, default=ImageType.BASIC)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.orig_image.name)
        super(BlogImages, self).save(*args, **kwargs)

    def __str__(self):
        return '{}({})'.format(self.name, self.pk)


class Tag(models.Model):
    tag_name = models.CharField(max_length=20, unique=True)
    tag_name_bn = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.tag_name


class BlogPost(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0
        PUBLISHED = 1

    title = models.CharField(max_length=200, null=False)
    author = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user), blank=True)
    hero_image = models.ForeignKey(BlogImages, on_delete=models.SET_NULL, null=True, blank=True, related_name="hero")
    thumbnail = models.ForeignKey(BlogImages, on_delete=models.SET_NULL, null=True, blank=True, related_name="thumbnail")
    body = models.TextField()
    short_desc = models.CharField(max_length=280, null=True, blank=True, verbose_name="Short Description")
    slug = models.SlugField(max_length=250, allow_unicode=True, unique=True, blank=True)
    tag = models.ManyToManyField(Tag)
    status = models.IntegerField(choices=Status.choices, default=Status.DRAFT)
    publish_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    visited_count = models.IntegerField(default=0)
    claps_count = models.IntegerField(default=0)
    minutes_to_read = models.IntegerField(default=0)
    remarks = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == BlogPost.Status.PUBLISHED:
            self.publish_date = timezone.now()
        super(BlogPost, self).save(*args, **kwargs)

    def __str__(self):
        return self.title
