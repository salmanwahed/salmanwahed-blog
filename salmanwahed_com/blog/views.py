import logging
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist

from .models import BlogPost
from django.conf import settings
from pathlib import Path

logger = logging.getLogger('default')


def blog_home(request):
    blogs = BlogPost.objects.select_related('thumbnail').prefetch_related('tag').filter(status=BlogPost.Status.PUBLISHED).order_by('-created_at')
    # blogs = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).order_by('-created_at')
    paginator = Paginator(blogs, settings.PAGINATION_ITEM_COUNT)
    show_pagination = True if paginator.num_pages > 1 else False
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/blog_list.html', dict(page_obj=page_obj, show_pagination=show_pagination))


def post_detail(request, id, slug=None):
    logger.info('Creating Blog Detail View. ID: {}'.format(id))
    try:
        blog = BlogPost.objects.select_related('hero_image', 'thumbnail').prefetch_related('tag').get(pk=id, status=BlogPost.Status.PUBLISHED)
    except ObjectDoesNotExist as ex:
        logger.exception(ex)
        response = render(request, 'blog/error/404.html')
        response.status_code = 404
        return response
    else:
        blog.visited_count += 1
        blog.save()
    return render(request, 'blog/blog.html', dict(blog=blog))


@login_required
def post_preview(request, id, slug=None):
    blog = get_object_or_404(BlogPost, pk=id, status=BlogPost.Status.DRAFT)
    return render(request, 'blog/blog.html', dict(blog=blog))


def tagged_posts(request, tag):
    logger.info('Clicked Tag: {}'.format(tag))
    blogs = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED, tag__tag_name=tag).order_by('-created_at')
    paginator = Paginator(blogs, settings.PAGINATION_ITEM_COUNT)
    show_pagination = True if paginator.num_pages > 1 else False
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/blog_list.html', dict(page_obj=page_obj, show_pagination=show_pagination))


def page_not_found(request, *args, **kwargs):
    logger.error('Error 404')
    response = render(request, 'blog/error/404.html')
    response.status_code = 404
    return response


def server_error(request, *args, **kwargs):
    logger.error('Error 500')
    response = render(request, 'blog/error/500.html')
    response.status_code = 500
    return response


class AboutView(TemplateView):
    template_name = 'blog/pages/about.html'

    def get(self, request, *args, **kwargs):
        logger.info('Creating About View')
        return super(AboutView, self).get(request, *args, **kwargs)


def serve_text_file(request, filename):
    file_path = settings.BASE_DIR.joinpath('text_files').joinpath(filename)
    logger.info(file_path)
    if Path.exists(file_path):
        with open(file_path, 'r') as fp:
            content = fp.read()
        return HttpResponse(content, content_type="text/plain")
    return page_not_found(request)