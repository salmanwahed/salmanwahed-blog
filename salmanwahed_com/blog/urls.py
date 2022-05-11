from django.urls import path, re_path
from . import views

app_name = 'blog'

urlpatterns = [
    # /blog/
    path('', views.homepage, name='homepage'),
    re_path(r'post/(?P<id>\d+)(?:/(?P<slug>[-\w]+))?/$', views.post_detail, name='blog_detail'),
    path('posts/tagged/<str:tag>/', views.tagged_posts, name='tagged_posts'),
    path('post/preview/<int:id>', views.post_preview, name='preview_post')
]