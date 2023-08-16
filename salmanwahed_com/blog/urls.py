from django.urls import path, re_path
from . import views

app_name = 'blog'

urlpatterns = [
    # /blog/
    path('', views.blog_home, name='blog_home'),
    re_path(r'post/(?P<id>\d+)(?:/(?P<slug>[-\w]+))?/$', views.post_detail, name='blog_detail'),
    path('posts/tagged/<str:tag>/', views.tagged_posts, name='tagged_posts'),
    path('post/preview/<int:id>', views.post_preview, name='preview_post'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('clear-cache/', views.clear_cache, name='clear-blog-cache'),
    path('.well-known/pki-validation/<str:filename>', views.serve_text_file, name='pki-validation')
]