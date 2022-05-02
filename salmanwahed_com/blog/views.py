from django.shortcuts import render
from .models import BlogPost
from django.shortcuts import get_object_or_404


# Create your views here.

def homepage(request):
    blogs = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).order_by('-created_at')
    return render(request, 'blog/blog_list.html', dict(blogs=blogs))


def post_detail(request, id, slug=None):
    blog = get_object_or_404(BlogPost, pk=id)
    blog.visited_count += 1
    blog.save()
    return render(request, 'blog/blog.html', dict(blog=blog))


def tagged_posts(request, tag):
    blogs = BlogPost.objects.filter(tag__tag_name=tag)
    return render(request, 'blog/blog_list.html', dict(blogs=blogs))
