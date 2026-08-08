from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import BlogPost, Tag
from blog.templatetags.blog_extras import minutes_to_read, render_body

# The real cache is Redis and the list/detail views are wrapped in cache_page.
# Swapping in locmem keeps one test's response from being served to the next.
LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "blog-tests",
    }
}


def make_post(**kwargs):
    author = kwargs.pop("author", None) or User.objects.create_user("writer", password="x")
    defaults = {
        "title": "A Post",
        "author": author,
        "body": "Hello world",
        "body_format": BlogPost.BodyFormat.MARKDOWN,
        "status": BlogPost.Status.PUBLISHED,
        "short_desc": "Short description.",
    }
    defaults.update(kwargs)
    return BlogPost.objects.create(**defaults)


class RenderBodyTests(TestCase):
    def test_html_post_passes_through_untouched(self):
        """A legacy CKEditor post must render exactly as stored."""
        stored = '<p>Already <strong>HTML</strong>.</p>\n<div class="gist">x</div>'
        post = make_post(body=stored, body_format=BlogPost.BodyFormat.HTML)

        self.assertEqual(render_body(post), stored)

    def test_html_post_is_not_markdown_escaped(self):
        """Markdown would mangle underscores and asterisks inside HTML."""
        post = make_post(body="<p>a_b_c and *stars*</p>", body_format=BlogPost.BodyFormat.HTML)

        rendered = render_body(post)
        self.assertIn("a_b_c", rendered)
        self.assertIn("*stars*", rendered)
        self.assertNotIn("<em>", rendered)

    def test_markdown_post_is_converted(self):
        post = make_post(body="# Title\n\nSome **bold** text.")

        rendered = render_body(post)
        self.assertIn("<strong>bold</strong>", rendered)
        self.assertIn("Title", rendered)

    def test_fenced_code_block_is_highlighted(self):
        post = make_post(body='```python\nprint("hi")\n```')

        rendered = render_body(post)
        self.assertIn("codehilite", rendered)
        self.assertIn("<pre", rendered)

    def test_markdown_tables_render(self):
        post = make_post(body="| a | b |\n|---|---|\n| 1 | 2 |")

        self.assertIn("<table>", render_body(post))

    def test_body_is_rendered_once_per_object(self):
        post = make_post(body="# Heading")

        first = render_body(post)
        # Mutating the source after the first render proves the cached value is
        # reused rather than recomputed on every call.
        post.body = "# Different"
        self.assertEqual(render_body(post), first)


class MinutesToReadTests(TestCase):
    def test_counts_words_not_markdown_syntax(self):
        post = make_post(body="# " + "word " * 180)

        self.assertEqual(minutes_to_read(post), "1 minute read")

    def test_pluralises_above_one_minute(self):
        post = make_post(body="word " * 400)

        self.assertEqual(minutes_to_read(post), "3 minutes read")

    def test_reads_html_posts(self):
        post = make_post(body="<p>" + "word " * 180 + "</p>", body_format=BlogPost.BodyFormat.HTML)

        self.assertEqual(minutes_to_read(post), "1 minute read")


class BodyFormatDefaultTests(TestCase):
    def test_new_posts_default_to_markdown(self):
        author = User.objects.create_user("someone", password="x")
        post = BlogPost.objects.create(title="T", author=author, body="x")

        self.assertEqual(post.body_format, BlogPost.BodyFormat.MARKDOWN)


@override_settings(CACHES=LOCMEM_CACHE)
class BlogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user("writer", password="x")
        cls.tag = Tag.objects.create(tag_name="python", color_code="#3f8a7e")
        cls.post = make_post(author=cls.author, title="Indexed Post")
        cls.post.tag.add(cls.tag)

    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def test_blog_home_renders(self):
        response = self.client.get(reverse("blog:blog_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Indexed Post")

    def test_post_detail_renders(self):
        url = reverse("blog:blog_detail", kwargs={"id": self.post.id, "slug": self.post.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Indexed Post")

    def test_tagged_posts_renders_and_exposes_tag(self):
        response = self.client.get(reverse("blog:tagged_posts", args=["python"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tag"], "python")

    def test_about_renders(self):
        response = self.client.get(reverse("blog:about"))

        self.assertEqual(response.status_code, 200)

    def test_draft_post_detail_is_not_public(self):
        draft = make_post(author=self.author, title="Draft", slug="draft", status=BlogPost.Status.DRAFT)
        url = reverse("blog:blog_detail", kwargs={"id": draft.id, "slug": draft.slug})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_nav_is_present_on_every_page(self):
        """The shared base template replaced two per-app base templates."""
        response = self.client.get(reverse("blog:blog_home"))

        self.assertContains(response, 'class="navigation"')
        self.assertContains(response, "theme-toggle")
