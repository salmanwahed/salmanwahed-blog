from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import BlogPost


# Create your views here.

def homepage(request):
    blogs = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).order_by('-created_at')
    return render(request, 'blog/blog_list.html', dict(blogs=blogs))


def post_detail(request, id, slug=None):
    blog = get_object_or_404(BlogPost, pk=id, status=BlogPost.Status.PUBLISHED)
    blog.visited_count += 1
    blog.save()
    return render(request, 'blog/blog.html', dict(blog=blog))

@login_required
def post_preview(request, id, slug=None):
    blog = get_object_or_404(BlogPost, pk=id, status=BlogPost.Status.DRAFT)
    return render(request, 'blog/blog.html', dict(blog=blog))

def tagged_posts(request, tag):
    blogs = BlogPost.objects.filter(tag__tag_name=tag)
    return render(request, 'blog/blog_list.html', dict(blogs=blogs))


def page_not_found(request, *args, **kwargs):
    response = render(request, 'blog/error/404.html')
    response.status_code = 404
    return response


def server_error(request, *args, **kwargs):
    response = render(request, 'blog/error/500.html')
    response.status_code = 500
    return response