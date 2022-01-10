from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import get_user_model


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='anonymous', first_name='Anonymous', last_name='User')[0]


class BlogImages(models.Model):
    orig_image = models.ImageField(upload_to='images')
    compressed_image = models.URLField(null=True, blank=True)
    image_type = models.CharField(max_length=20,
                                  choices=[('HERO', 'Hero'), ("THUMBNAIL", 'Thumbnail'), ("REGULAR", "Regular")])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)


class Tag(models.Model):
    tag_name = models.CharField(max_length=20, unique=True)
    tag_name_bn = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.tag_name


class BlogPost(models.Model):
    title = models.CharField(max_length=200, null=False)
    author = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    hero_image = models.ForeignKey(BlogImages, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    slug = models.SlugField(max_length=250, allow_unicode=True, unique=True)
    tag = models.ManyToManyField(Tag)
    status = models.CharField(max_length=20, choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published')])
    publish_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    visited_count = models.IntegerField(null=True, blank=True)
    claps_count = models.IntegerField(null=True, blank=True)
    minutes_to_read = models.IntegerField(null=True, blank=True)
    remarks = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        if self.status == 'PUBLISHED':
            self.publish_date = timezone.now()
        super(BlogPost, self).save(*args, **kwargs)

    def __str__(self):
        return self.title
