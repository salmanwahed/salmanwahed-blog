from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import BlogPost, Tag
from .templatetags.blog_extras import minutes_to_read

DUMMY_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


class TagModelTest(TestCase):
    def test_str(self):
        tag = Tag.objects.create(tag_name='Python')
        self.assertEqual(str(tag), 'Python')

    def test_unique_tag_name(self):
        Tag.objects.create(tag_name='Python')
        with self.assertRaises(Exception):
            Tag.objects.create(tag_name='Python')


class BlogPostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='pass')

    def test_slug_auto_generated_from_title(self):
        post = BlogPost.objects.create(title='Hello World', author=self.user, body='content')
        self.assertEqual(post.slug, 'hello-world')

    def test_explicit_slug_not_overridden(self):
        post = BlogPost.objects.create(title='Hello World', author=self.user, body='content', slug='my-custom-slug')
        self.assertEqual(post.slug, 'my-custom-slug')

    def test_publish_date_set_when_published(self):
        post = BlogPost.objects.create(
            title='Live Post', author=self.user, body='content', status=BlogPost.Status.PUBLISHED
        )
        self.assertIsNotNone(post.publish_date)

    def test_publish_date_none_for_draft(self):
        post = BlogPost.objects.create(title='Draft', author=self.user, body='content')
        self.assertIsNone(post.publish_date)

    def test_default_status_is_draft(self):
        post = BlogPost.objects.create(title='Test', author=self.user, body='content')
        self.assertEqual(post.status, BlogPost.Status.DRAFT)

    def test_str(self):
        post = BlogPost.objects.create(title='My Post', author=self.user, body='content')
        self.assertEqual(str(post), 'My Post')

    def test_visited_count_defaults_to_zero(self):
        post = BlogPost.objects.create(title='Test', author=self.user, body='content')
        self.assertEqual(post.visited_count, 0)


@override_settings(CACHES=DUMMY_CACHE)
class BlogHomeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='pass')
        self.published = BlogPost.objects.create(
            title='Published', author=self.user, body='content', status=BlogPost.Status.PUBLISHED
        )
        self.draft = BlogPost.objects.create(
            title='Draft', author=self.user, body='content', status=BlogPost.Status.DRAFT
        )

    def test_returns_200(self):
        response = self.client.get(reverse('blog:blog_home'))
        self.assertEqual(response.status_code, 200)

    def test_only_published_posts_shown(self):
        response = self.client.get(reverse('blog:blog_home'))
        posts = list(response.context['page_obj'])
        self.assertIn(self.published, posts)
        self.assertNotIn(self.draft, posts)


@override_settings(CACHES=DUMMY_CACHE)
class PostDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='pass')
        self.published = BlogPost.objects.create(
            title='Published Post', author=self.user, body='content', status=BlogPost.Status.PUBLISHED
        )
        self.draft = BlogPost.objects.create(
            title='Draft Post', author=self.user, body='content', status=BlogPost.Status.DRAFT
        )

    def _detail_url(self, post):
        return f'/post/{post.pk}/{post.slug}/'

    def test_published_post_returns_200(self):
        response = self.client.get(self._detail_url(self.published))
        self.assertEqual(response.status_code, 200)

    def test_draft_post_returns_404(self):
        response = self.client.get(self._detail_url(self.draft))
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_post_returns_404(self):
        response = self.client.get('/post/99999/no-such-post/')
        self.assertEqual(response.status_code, 404)

    def test_visit_count_increments_on_view(self):
        self.client.get(self._detail_url(self.published))
        self.published.refresh_from_db()
        self.assertEqual(self.published.visited_count, 1)


class PostPreviewViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='pass')
        self.draft = BlogPost.objects.create(
            title='Draft Post', author=self.user, body='content', status=BlogPost.Status.DRAFT
        )
        self.published = BlogPost.objects.create(
            title='Live Post', author=self.user, body='content', status=BlogPost.Status.PUBLISHED
        )

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse('blog:preview_post', args=[self.draft.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_logged_in_user_can_preview_draft(self):
        self.client.login(username='author', password='pass')
        response = self.client.get(reverse('blog:preview_post', args=[self.draft.pk]))
        self.assertEqual(response.status_code, 200)

    def test_preview_of_published_post_returns_404(self):
        self.client.login(username='author', password='pass')
        response = self.client.get(reverse('blog:preview_post', args=[self.published.pk]))
        self.assertEqual(response.status_code, 404)


@override_settings(CACHES=DUMMY_CACHE)
class TaggedPostsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='pass')
        self.tag = Tag.objects.create(tag_name='Django')
        self.tagged = BlogPost.objects.create(
            title='Django Post', author=self.user, body='content', status=BlogPost.Status.PUBLISHED
        )
        self.tagged.tag.add(self.tag)
        self.untagged = BlogPost.objects.create(
            title='Other Post', author=self.user, body='content', status=BlogPost.Status.PUBLISHED
        )

    def test_returns_200(self):
        response = self.client.get(reverse('blog:tagged_posts', args=['Django']))
        self.assertEqual(response.status_code, 200)

    def test_only_posts_with_that_tag_shown(self):
        response = self.client.get(reverse('blog:tagged_posts', args=['Django']))
        posts = list(response.context['page_obj'])
        self.assertIn(self.tagged, posts)
        self.assertNotIn(self.untagged, posts)

    def test_draft_posts_excluded(self):
        draft = BlogPost.objects.create(
            title='Draft Django Post', author=self.user, body='content', status=BlogPost.Status.DRAFT
        )
        draft.tag.add(self.tag)
        response = self.client.get(reverse('blog:tagged_posts', args=['Django']))
        posts = list(response.context['page_obj'])
        self.assertNotIn(draft, posts)


class ClearCacheViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='pass')

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse('blog:clear-blog-cache'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_logged_in_redirects_to_home(self):
        self.client.login(username='author', password='pass')
        response = self.client.get(reverse('blog:clear-blog-cache'))
        self.assertRedirects(response, reverse('blog:blog_home'))


@override_settings(CACHES=DUMMY_CACHE)
class AboutViewTest(TestCase):
    def test_returns_200(self):
        response = self.client.get(reverse('blog:about'))
        self.assertEqual(response.status_code, 200)


@override_settings(WPM_READ=180)
class MinutesToReadTagTest(TestCase):
    def test_single_minute(self):
        # 180 words at 180 WPM = exactly 1 minute
        body = '<p>{}</p>'.format(' '.join(['word'] * 180))
        self.assertEqual(minutes_to_read(body), '1 minute read')

    def test_plural_minutes(self):
        # 360 words at 180 WPM = 2 minutes
        body = '<p>{}</p>'.format(' '.join(['word'] * 360))
        self.assertEqual(minutes_to_read(body), '2 minutes read')

    def test_rounds_up(self):
        # 181 words at 180 WPM = ceil(1.005...) = 2 minutes
        body = '<p>{}</p>'.format(' '.join(['word'] * 181))
        self.assertEqual(minutes_to_read(body), '2 minutes read')
