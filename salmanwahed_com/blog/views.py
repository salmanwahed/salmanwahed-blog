import logging
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.cache import cache_page, never_cache
from django.views.generic import TemplateView
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator


from .apps import BlogConfig
from .models import BlogPost

logger = logging.getLogger('default')


@cache_page(timeout=15 * 60, key_prefix=BlogConfig.name)
def blog_home(request):
    blogs = BlogPost.objects.select_related('thumbnail').prefetch_related('tag').filter(
        status=BlogPost.Status.PUBLISHED).order_by('-created_at')
    # blogs = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).order_by('-created_at')
    paginator = Paginator(blogs, settings.PAGINATION_ITEM_COUNT)
    show_pagination = True if paginator.num_pages > 1 else False
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/blog_list.html', dict(page_obj=page_obj, show_pagination=show_pagination))


@cache_page(timeout=15 * 60, key_prefix=BlogConfig.name)
def post_detail(request, id, slug=None):
    logger.info('Creating Blog Detail View. ID: {}'.format(id))
    try:
        blog = BlogPost.objects.select_related('hero_image', 'thumbnail').prefetch_related('tag').get(pk=id,
                                                                                                      status=BlogPost.Status.PUBLISHED)
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


@cache_page(timeout=15 * 60, key_prefix=BlogConfig.name)
def tagged_posts(request, tag):
    logger.info('Clicked Tag: {}'.format(tag))
    blogs = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED, tag__tag_name=tag).order_by('-created_at')
    paginator = Paginator(blogs, settings.PAGINATION_ITEM_COUNT)
    show_pagination = True if paginator.num_pages > 1 else False
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/blog_list.html', dict(page_obj=page_obj, show_pagination=show_pagination))


@never_cache
def page_not_found(request, *args, **kwargs):
    logger.error('Error 404')
    response = render(request, 'blog/error/404.html')
    response.status_code = 404
    return response


@never_cache
def server_error(request, *args, **kwargs):
    logger.error('Error 500')
    response = render(request, 'blog/error/500.html')
    response.status_code = 500
    return response


class AboutView(TemplateView):
    template_name = 'blog/pages/about.html'

    @method_decorator(cache_page(timeout=60 * 60, key_prefix=BlogConfig.name))  # Cache for 15 minutes
    def dispatch(self, request, *args, **kwargs):
        logger.info('Creating About View')
        return super().dispatch(request, *args, **kwargs)


def serve_text_file(request, filename):
    file_path = settings.BASE_DIR.joinpath('text_files').joinpath(filename)
    logger.info(file_path)
    if Path.exists(file_path):
        with open(file_path, 'r') as fp:
            content = fp.read()
        return HttpResponse(content, content_type="text/plain")
    return page_not_found(request)


@never_cache
@login_required
def clear_cache(request):
    cache.clear()
    return redirect(reverse('blog:blog_home'))
