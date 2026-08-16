import shutil
import tempfile
from pathlib import Path

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from blog.admin import BlogPostAdmin
from blog.models import BlogImages, BlogPost, Tag, get_sentinel_user
from blog.templatetags.blog_extras import minutes_to_read, render_body
from blog.views import page_not_found, server_error

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


class SentinelUserTests(TestCase):
    """author is SET(get_sentinel_user), so deleting a user must not lose posts."""

    def test_sentinel_user_is_reused_not_duplicated(self):
        first = get_sentinel_user()
        second = get_sentinel_user()

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.username, "anonymous")


@override_settings(CDN_URL="https://cdn.example.com/", USE_CDN=False)
class BlogImagesTests(TestCase):
    def test_name_defaults_to_the_uploaded_filename(self):
        image = BlogImages.objects.create(orig_image="blog/photo.png")

        self.assertEqual(image.name, "photo.png")

    def test_explicit_name_is_kept(self):
        image = BlogImages.objects.create(name="Chosen", orig_image="blog/photo.png")

        self.assertEqual(image.name, "Chosen")

    def test_image_url_serves_locally_when_cdn_is_off(self):
        image = BlogImages.objects.create(orig_image="blog/photo.png")

        self.assertEqual(image.image_url, "/upload/blog/photo.png")

    @override_settings(USE_CDN=True)
    def test_image_url_serves_from_cdn_when_enabled(self):
        image = BlogImages.objects.create(orig_image="blog/photo.png")

        self.assertEqual(image.image_url, "https://cdn.example.com/upload/blog/photo.png")

    def test_compressed_url_is_computed_once_and_stored(self):
        """The CDN URL is derived lazily, then persisted so it is not rebuilt."""
        image = BlogImages.objects.create(orig_image="blog/photo.png")
        self.assertFalse(image.compressed_image)

        # Accessing the property is the action under test: it derives the CDN
        # URL and writes it back.
        self.assertEqual(image.image_url, "/upload/blog/photo.png")

        image.refresh_from_db()
        self.assertEqual(image.compressed_image, "https://cdn.example.com/upload/blog/photo.png")

    @override_settings(USE_CDN=True)
    def test_stored_compressed_url_is_reused_not_recomputed(self):
        """Once stored, the CDN URL is returned as-is even if CDN_URL changes."""
        image = BlogImages.objects.create(
            orig_image="blog/photo.png",
            compressed_image="https://old-cdn.example.com/photo.png",
        )

        self.assertEqual(image.image_url, "https://old-cdn.example.com/photo.png")

    def test_orig_image_url_property(self):
        image = BlogImages.objects.create(orig_image="blog/photo.png")

        self.assertEqual(image.orig_image_url, "/upload/blog/photo.png")

    def test_admin_preview_renders_an_img_tag(self):
        image = BlogImages.objects.create(orig_image="blog/photo.png")

        self.assertIn('<img src="/upload/blog/photo.png"', image.image_preview())

    def test_str_includes_name_and_pk(self):
        image = BlogImages.objects.create(orig_image="blog/photo.png")

        self.assertEqual(str(image), f"photo.png({image.pk})")


class BlogModelStringTests(TestCase):
    def test_tag_str_is_the_tag_name(self):
        self.assertEqual(str(Tag.objects.create(tag_name="django")), "django")

    def test_tag_colour_swatch_uses_the_colour_code(self):
        tag = Tag.objects.create(tag_name="django", color_code="#0c4b33")

        self.assertIn("background-color:#0c4b33", tag.tag_color())

    def test_post_str_is_the_title(self):
        self.assertEqual(str(make_post(title="Readable")), "Readable")

    def test_draft_offers_a_preview_link_in_admin(self):
        draft = make_post(title="Unpublished", status=BlogPost.Status.DRAFT)

        self.assertIn(f"/post/preview/{draft.id}", draft.blog_preview())

    def test_published_post_has_no_preview_link(self):
        published = make_post(title="Live", status=BlogPost.Status.PUBLISHED)

        self.assertIsNone(published.blog_preview())


@override_settings(CACHES=LOCMEM_CACHE)
class PostPreviewTests(TestCase):
    """Draft preview is the only way to see unpublished work, so it must be gated."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user("previewer", password="secret")
        cls.draft = make_post(author=cls.author, title="Hidden", slug="hidden", status=BlogPost.Status.DRAFT)

    def test_anonymous_visitor_is_redirected_to_login(self):
        response = self.client.get(reverse("blog:preview_post", args=[self.draft.id]))

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("Hidden", response.content.decode())

    def test_logged_in_user_sees_the_draft(self):
        self.client.login(username="previewer", password="secret")

        response = self.client.get(reverse("blog:preview_post", args=[self.draft.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hidden")

    def test_published_post_is_not_previewable(self):
        """The view is for drafts only; a published id must not resolve here."""
        self.client.login(username="previewer", password="secret")
        published = make_post(author=self.author, title="Live", slug="live")

        response = self.client.get(reverse("blog:preview_post", args=[published.id]))

        self.assertEqual(response.status_code, 404)


@override_settings(CACHES=LOCMEM_CACHE)
class ClearCacheTests(TestCase):
    def test_anonymous_visitor_cannot_flush_the_cache(self):
        cache.set("keep-me", "value")

        response = self.client.get(reverse("blog:clear-blog-cache"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(cache.get("keep-me"), "value")

    def test_logged_in_user_flushes_and_is_sent_home(self):
        User.objects.create_user("staffer", password="secret")
        self.client.login(username="staffer", password="secret")
        cache.set("stale", "value")

        response = self.client.get(reverse("blog:clear-blog-cache"))

        self.assertRedirects(response, reverse("blog:blog_home"))
        self.assertIsNone(cache.get("stale"))


class ErrorHandlerTests(TestCase):
    """handler404/handler500 point at these, so they must render standalone."""

    def test_page_not_found_renders_with_404_status(self):
        response = page_not_found(RequestFactory().get("/nope/"))

        self.assertEqual(response.status_code, 404)

    def test_server_error_renders_with_500_status(self):
        response = server_error(RequestFactory().get("/boom/"))

        self.assertEqual(response.status_code, 500)


class ServeTextFileTests(TestCase):
    """Used for domain-validation files, which must be served verbatim."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        Path(self.tmp, "text_files").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, filename, content):
        Path(self.tmp, "text_files", filename).write_text(content, encoding="utf-8")

    def test_existing_file_is_served_as_plain_text(self):
        self._write("validation.txt", "token-abc123")

        with override_settings(BASE_DIR=Path(self.tmp)):
            response = self.client.get(reverse("blog:text-files", args=["validation.txt"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertEqual(response.content.decode(), "token-abc123")

    def test_missing_file_falls_back_to_404(self):
        with override_settings(BASE_DIR=Path(self.tmp)):
            response = self.client.get(reverse("blog:text-files", args=["absent.txt"]))

        self.assertEqual(response.status_code, 404)

    def test_pki_validation_path_serves_the_same_file(self):
        self._write("pki.txt", "pki-token")

        with override_settings(BASE_DIR=Path(self.tmp)):
            response = self.client.get(reverse("blog:pki-validation", args=["pki.txt"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "pki-token")


class BlogPostAdminTests(TestCase):
    """save_model fills in the fields an author should not have to set by hand."""

    def setUp(self):
        self.admin = BlogPostAdmin(BlogPost, AdminSite())
        self.user = User.objects.create_superuser("editor", "e@example.com", "secret")
        self.request = RequestFactory().post("/nimda/dehawnamlas/blog/blogpost/add/")
        self.request.user = self.user

    def _save(self, post):
        self.admin.save_model(self.request, post, form=None, change=False)
        return post

    def test_slug_is_derived_from_the_title_when_blank(self):
        post = self._save(BlogPost(title="A Post About Django", body="x", author=self.user))

        self.assertEqual(post.slug, "a-post-about-django")

    def test_existing_slug_is_left_alone(self):
        post = self._save(BlogPost(title="A Post", slug="chosen-slug", body="x", author=self.user))

        self.assertEqual(post.slug, "chosen-slug")

    def test_publishing_stamps_the_publish_date(self):
        post = self._save(BlogPost(title="Going Live", body="x", author=self.user, status=BlogPost.Status.PUBLISHED))

        self.assertIsNotNone(post.publish_date)

    def test_draft_is_not_stamped(self):
        post = self._save(BlogPost(title="Still Drafting", body="x", author=self.user, status=BlogPost.Status.DRAFT))

        self.assertIsNone(post.publish_date)

    def test_author_defaults_to_the_editing_user(self):
        post = self._save(BlogPost(title="Unattributed", body="x"))

        self.assertEqual(post.author, self.user)
