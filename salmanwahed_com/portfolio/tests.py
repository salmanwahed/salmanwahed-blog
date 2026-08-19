from smtplib import SMTPException
from unittest import mock
from uuid import uuid4

from django.core import mail
from django.core.cache import cache
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from portfolio.forms import ContactForm
from portfolio.models import AppPrivacyPolicy, Project, ProjectImage, ProjectStat, Tag
from portfolio.views import ContactView, ProjectListView

# ProjectListView and the policy/resume views are wrapped in cache_page. Any
# real backend lets a page cached by one test class be served to the next, which
# made these tests pass alone and fail in a full run. DummyCache stores nothing,
# so every request renders from the database and the assertions describe the
# template rather than whatever ran first.
NO_PAGE_CACHE = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}


def get_projects_page(client):
    """GET /portfolio/ with a URL no other test can share.

    ProjectListView is wrapped in cache_page, and overriding CACHES alone did
    not reliably stop a page cached by one test class being served to the next
    -- these tests passed in isolation and failed in a full run, showing objects
    that were not in the database. cache_page keys on the full path including
    the query string, so a unique one per request cannot collide. The view
    ignores the parameter.
    """
    return client.get(f"{reverse('portfolio:portfolio_view')}?t={uuid4().hex}")


# The contact throttle counts submissions in the cache, so those tests need a
# backend that actually retains values.
LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "portfolio-tests",
    }
}

VALID_SUBMISSION = {
    "name": "Aisha Rahman",
    "email": "aisha@example.com",
    "subject": "Consulting enquiry",
    "message": "I would like to discuss a backend project with you.",
    "website": "",
}


@override_settings(CACHES=NO_PAGE_CACHE)
class ProjectListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.professional = Project.objects.create(
            name="TallyKhata",
            category=Project.Category.PROFESSIONAL,
            meta_primary="Senior Software Engineer",
            meta_secondary="2019 — Present",
            is_featured=True,
            description="Digital bookkeeping for small businesses.",
            project_weight=10,
        )
        ProjectStat.objects.create(project=cls.professional, label="Users", value="8M+", order=1)
        cls.personal = Project.objects.create(
            name="SadaSidhe",
            category=Project.Category.PERSONAL,
            short_description="A simple notes app.",
        )

    def setUp(self):
        cache.clear()

    def test_featured_work_leads_and_the_rest_is_filed_by_category(self):
        """Asserted against rendered HTML rather than response.context.

        The view is wrapped in cache_page, and the test client's context capture
        is not dependable through that decorator once a full suite has run.
        """
        response = get_projects_page(self.client)
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn(">Featured<", html)
        self.assertIn(">Personal Works<", html)

        featured_band = html.split('class="project-grid"')[0]
        grids = html.split('class="project-grid"')[1]

        # TallyKhata is featured, so it leads the page rather than sitting in
        # the professional section.
        self.assertIn("TallyKhata", featured_band)
        self.assertNotIn("TallyKhata", grids)
        self.assertIn("SadaSidhe", grids)
        self.assertNotIn("SadaSidhe", featured_band)

    def test_context_groups_featured_separately_from_the_categories(self):
        """The split itself, checked on the view rather than through the client."""
        view = ProjectListView()
        view.request = RequestFactory().get("/portfolio/")
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        self.assertEqual(list(context["featured_projects"]), [self.professional])
        self.assertEqual(list(context["professional_projects"]), [], "featured work is not listed twice")
        self.assertEqual(list(context["personal_projects"]), [self.personal])
        self.assertEqual(context["active"], "projects")

    def test_featured_card_shows_badge_role_and_stats(self):
        response = get_projects_page(self.client)

        self.assertContains(response, "Featured")
        self.assertContains(response, "Senior Software Engineer")
        self.assertContains(response, "8M+")
        self.assertContains(response, "Users")

    def test_personal_project_appears_in_grid(self):
        response = get_projects_page(self.client)

        self.assertContains(response, "SadaSidhe")
        self.assertContains(response, "A simple notes app.")

    def test_projects_default_to_personal(self):
        """Existing rows predate the category field and must land in the grid."""
        project = Project.objects.create(name="Legacy")

        self.assertEqual(project.category, Project.Category.PERSONAL)


class ContactFormTests(TestCase):
    def test_valid_submission_passes(self):
        self.assertTrue(ContactForm(data=VALID_SUBMISSION).is_valid())

    def test_filled_honeypot_is_rejected(self):
        payload = dict(VALID_SUBMISSION, website="http://spam.example")

        form = ContactForm(data=payload)

        self.assertFalse(form.is_valid())
        self.assertIn("website", form.errors)

    def test_very_short_message_is_rejected(self):
        form = ContactForm(data=dict(VALID_SUBMISSION, message="hi"))

        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)

    def test_invalid_email_is_rejected(self):
        form = ContactForm(data=dict(VALID_SUBMISSION, email="not-an-email"))

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


@override_settings(
    CACHES=LOCMEM_CACHE,
    CONTACT_EMAIL="hello@example.com",
    CONTACT_RATE_LIMIT=2,
    CONTACT_FORM_ENABLED=True,
)
class ContactViewTests(TestCase):
    """The form path, exercised with CONTACT_FORM_ENABLED on.

    The flag is off in production for now, but these still guard the behaviour
    so turning it back on is a one-line change rather than a rewrite.
    """

    def setUp(self):
        cache.clear()
        mail.outbox = []

    def test_get_renders_the_form(self):
        response = self.client.get(reverse("portfolio:contact"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "contact-form")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_valid_post_sends_mail_and_shows_success(self):
        response = self.client.post(reverse("portfolio:contact"), VALID_SUBMISSION)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["sent"])
        self.assertContains(response, "form-success")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["hello@example.com"])
        self.assertIn("Consulting enquiry", mail.outbox[0].subject)
        self.assertIn("aisha@example.com", mail.outbox[0].body)

    def test_reply_to_is_the_sender_not_ourselves(self):
        """Hitting reply on the notification must reach the enquirer."""
        self.client.post(reverse("portfolio:contact"), VALID_SUBMISSION)

        self.assertEqual(mail.outbox[0].reply_to, ["aisha@example.com"])
        self.assertNotEqual(mail.outbox[0].from_email, "aisha@example.com")

    def test_honeypot_submission_sends_no_mail(self):
        payload = dict(VALID_SUBMISSION, website="http://spam.example")

        response = self.client.post(reverse("portfolio:contact"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_throttle_blocks_after_the_limit(self):
        url = reverse("portfolio:contact")

        for _ in range(2):
            self.client.post(url, VALID_SUBMISSION)
        self.assertEqual(len(mail.outbox), 2)

        response = self.client.post(url, VALID_SUBMISSION)

        self.assertEqual(len(mail.outbox), 2, "third send should have been throttled")
        self.assertContains(response, "Too many messages")

    def test_invalid_submission_does_not_consume_throttle_allowance(self):
        url = reverse("portfolio:contact")

        self.client.post(url, dict(VALID_SUBMISSION, message="hi"))
        self.client.post(url, VALID_SUBMISSION)
        self.client.post(url, VALID_SUBMISSION)

        self.assertEqual(len(mail.outbox), 2)

    def test_response_is_not_cached(self):
        response = self.client.get(reverse("portfolio:contact"))

        self.assertIn("no-cache", response["Cache-Control"])


@override_settings(CACHES=LOCMEM_CACHE, CONTACT_EMAIL="hello@example.com", CONTACT_FORM_ENABLED=False)
class ContactFormDisabledTests(TestCase):
    """Current production shape: mailto only, no form."""

    def setUp(self):
        cache.clear()
        mail.outbox = []

    def test_form_is_not_rendered(self):
        response = self.client.get(reverse("portfolio:contact"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "contact-form")
        self.assertNotContains(response, "Send message")

    def test_email_address_is_still_offered(self):
        response = self.client.get(reverse("portfolio:contact"))

        self.assertContains(response, "mailto:hello@example.com")

    def test_post_is_ignored_and_sends_nothing(self):
        """Bots probing the URL must not reach the send path."""
        response = self.client.post(reverse("portfolio:contact"), VALID_SUBMISSION)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(response.context["sent"])


@override_settings(CACHES=NO_PAGE_CACHE)
class StaticPageTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_resume_renders(self):
        response = self.client.get(reverse("portfolio:resume"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Salman M Wahed")

    def test_resume_url_is_at_site_root(self):
        self.assertEqual(reverse("portfolio:resume"), "/resume/")

    def test_contact_url_is_at_site_root(self):
        self.assertEqual(reverse("portfolio:contact"), "/contact/")

    def test_existing_portfolio_url_is_unchanged(self):
        self.assertEqual(reverse("portfolio:portfolio_view"), "/portfolio/")


@override_settings(CDN_URL="https://cdn.example.com/", USE_CDN=False)
class ProjectImageTests(TestCase):
    def test_name_defaults_to_the_uploaded_filename(self):
        image = ProjectImage.objects.create(orig_image="portfolio/logo.png")

        self.assertEqual(image.name, "logo.png")

    def test_image_url_serves_locally_when_cdn_is_off(self):
        image = ProjectImage.objects.create(orig_image="portfolio/logo.png")

        self.assertEqual(image.image_url, "/upload/portfolio/logo.png")

    @override_settings(USE_CDN=True)
    def test_image_url_serves_from_cdn_when_enabled(self):
        image = ProjectImage.objects.create(orig_image="portfolio/logo.png")

        self.assertEqual(image.image_url, "https://cdn.example.com/upload/portfolio/logo.png")

    @override_settings(USE_CDN=True)
    def test_stored_compressed_url_is_reused_not_recomputed(self):
        """Once stored, the CDN URL is returned as-is even if CDN_URL changes."""
        image = ProjectImage.objects.create(
            orig_image="portfolio/logo.png",
            compressed_image="https://old-cdn.example.com/logo.png",
        )

        self.assertEqual(image.image_url, "https://old-cdn.example.com/logo.png")

    def test_admin_preview_renders_an_img_tag(self):
        image = ProjectImage.objects.create(orig_image="portfolio/logo.png")

        self.assertIn('<img src="/upload/portfolio/logo.png"', image.image_preview())

    def test_str_includes_name_and_pk(self):
        image = ProjectImage.objects.create(orig_image="portfolio/logo.png")

        self.assertEqual(str(image), f"logo.png({image.pk})")


class PortfolioModelStringTests(TestCase):
    def test_tag_str_is_the_tag_name(self):
        self.assertEqual(str(Tag.objects.create(tag_name="kotlin")), "kotlin")

    def test_tag_colour_swatch_uses_the_colour_code(self):
        tag = Tag.objects.create(tag_name="kotlin", color_code="#7f52ff")

        self.assertIn("background-color:#7f52ff", tag.tag_color())

    def test_project_str_is_the_name(self):
        self.assertEqual(str(Project.objects.create(name="Rate-Sage")), "Rate-Sage")

    def test_project_stat_str_pairs_value_and_label(self):
        project = Project.objects.create(name="Rate-Sage")
        stat = ProjectStat.objects.create(project=project, label="Users", value="8M+")

        self.assertEqual(str(stat), "8M+ Users")

    def test_privacy_policy_slug_must_be_unique(self):
        """The slug is the public URL key, so a duplicate must not be storable."""
        AppPrivacyPolicy.objects.create(name="Rate-Sage Policy", slug="rate-sage", body="Body")

        # atomic() keeps the failed INSERT from poisoning the test's outer
        # transaction, which would break teardown.
        with self.assertRaises(IntegrityError), transaction.atomic():
            AppPrivacyPolicy.objects.create(name="Another", slug="rate-sage", body="Body")


@override_settings(CACHES=NO_PAGE_CACHE)
class AppPrivacyPolicyViewTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_policy_is_served_by_slug(self):
        AppPrivacyPolicy.objects.create(name="Rate-Sage Policy", slug="rate-sage", body="We store nothing.")

        response = self.client.get(reverse("portfolio:app_privacy_policy", args=["rate-sage"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rate-Sage Policy")

    def test_unknown_slug_is_404(self):
        response = self.client.get(reverse("portfolio:app_privacy_policy", args=["does-not-exist"]))

        self.assertEqual(response.status_code, 404)


@override_settings(
    CACHES=LOCMEM_CACHE,
    CONTACT_EMAIL="hello@example.com",
    CONTACT_RATE_LIMIT=5,
    CONTACT_FORM_ENABLED=True,
)
class ContactSendFailureTests(TestCase):
    """An unreachable relay must not look like a delivered message."""

    def setUp(self):
        cache.clear()
        mail.outbox = []

    def test_smtp_failure_is_reported_and_not_counted_as_sent(self):
        with mock.patch(
            "portfolio.views.EmailMessage.send",
            side_effect=SMTPException("relay unreachable"),
        ):
            response = self.client.post(reverse("portfolio:contact"), VALID_SUBMISSION)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["sent"])
        self.assertContains(response, "could not be sent")
        self.assertEqual(len(mail.outbox), 0)

    def test_failed_send_does_not_consume_the_throttle_allowance(self):
        """A broken relay must not lock the visitor out of retrying later."""
        with mock.patch(
            "portfolio.views.EmailMessage.send",
            side_effect=SMTPException("relay unreachable"),
        ):
            self.client.post(reverse("portfolio:contact"), VALID_SUBMISSION)

        self.client.post(reverse("portfolio:contact"), VALID_SUBMISSION)

        self.assertEqual(len(mail.outbox), 1, "the retry should still have been allowed through")


@override_settings(CACHES=LOCMEM_CACHE, CONTACT_FORM_ENABLED=True)
class ClientIpTests(TestCase):
    """The throttle is per-IP, so it must read the header nginx actually sets."""

    def setUp(self):
        cache.clear()

    def _view_for(self, **headers):
        view = ContactView()
        view.request = RequestFactory().post(reverse("portfolio:contact"), **headers)
        return view

    def test_x_real_ip_is_preferred(self):
        view = self._view_for(HTTP_X_REAL_IP="203.0.113.7", REMOTE_ADDR="127.0.0.1")

        self.assertEqual(view._client_ip(), "203.0.113.7")

    def test_remote_addr_is_the_fallback(self):
        view = self._view_for(REMOTE_ADDR="198.51.100.4")

        self.assertEqual(view._client_ip(), "198.51.100.4")

    def test_throttle_key_is_scoped_per_ip(self):
        first = self._view_for(HTTP_X_REAL_IP="203.0.113.7")._throttle_key()
        second = self._view_for(HTTP_X_REAL_IP="203.0.113.8")._throttle_key()

        self.assertNotEqual(first, second)


@override_settings(CACHES=NO_PAGE_CACHE)
class FeaturedRenderingTests(TestCase):
    """is_featured decides the card shape, independently of category."""

    def setUp(self):
        cache.clear()

    def _html(self):
        return get_projects_page(self.client).content.decode()

    def test_featured_personal_project_gets_the_wide_card(self):
        Project.objects.create(
            name="SadaSidhe",
            category=Project.Category.PERSONAL,
            is_featured=True,
            description="A personal app worth showing off.",
        )

        html = self._html()

        featured_block = html.split('class="project-grid"')[0]
        self.assertIn("project-featured", html)
        self.assertIn("SadaSidhe", featured_block)

    def test_unfeatured_professional_project_goes_in_the_grid(self):
        Project.objects.create(
            name="Quiet Contract",
            category=Project.Category.PROFESSIONAL,
            is_featured=False,
            short_description="Not headline work.",
        )

        html = self._html()

        self.assertIn("project-card", html)
        self.assertIn("Quiet Contract", html.split('class="project-grid"')[1])

    def test_featured_personal_work_outranks_unfeatured_professional_work(self):
        """The whole point of the featured band: prominence beats category."""
        Project.objects.create(
            name="Personal Star",
            category=Project.Category.PERSONAL,
            is_featured=True,
        )
        Project.objects.create(
            name="Quiet Contract",
            category=Project.Category.PROFESSIONAL,
            is_featured=False,
        )

        html = self._html()

        self.assertLess(
            html.index("Personal Star"),
            html.index("Quiet Contract"),
            "a featured personal project must appear above unfeatured professional work",
        )

    def test_featured_projects_of_both_categories_share_the_band(self):
        Project.objects.create(name="Personal Star", category=Project.Category.PERSONAL, is_featured=True)
        Project.objects.create(name="Work Star", category=Project.Category.PROFESSIONAL, is_featured=True)

        html = self._html()
        band = html.split('<div class="group-label">')[1]

        self.assertTrue(band.startswith("Featured<"))
        self.assertIn("Personal Star", band)
        self.assertIn("Work Star", band)

    def test_featured_badge_shows_on_the_card(self):
        Project.objects.create(name="Badged", category=Project.Category.PERSONAL, is_featured=True)

        self.assertIn("Featured", self._html())


@override_settings(CACHES=NO_PAGE_CACHE)
class StatsEarnTheWideCardTests(TestCase):
    """Stats are the second route to the wide card: a grid card cannot show them."""

    def setUp(self):
        cache.clear()

    def _html(self):
        return get_projects_page(self.client).content.decode()

    def test_unflagged_project_with_stats_gets_the_wide_card(self):
        project = Project.objects.create(
            name="Quiet Contract",
            category=Project.Category.PROFESSIONAL,
            is_featured=False,
            description="No badge, but numbers worth showing.",
        )
        ProjectStat.objects.create(project=project, label="Users", value="8M+")

        html = self._html()

        self.assertIn("project-featured", html)
        self.assertIn("8M+", html, "the stats are the reason for the wide card, so they must render")
        self.assertNotIn("project-card", html, "it should not also appear as a grid card")

    def test_the_card_is_not_labelled_featured_without_the_flag(self):
        """A card shown for its numbers must not claim to be featured."""
        project = Project.objects.create(name="Quiet Contract", is_featured=False)
        ProjectStat.objects.create(project=project, label="Users", value="8M+")

        self.assertNotIn(">Featured<", self._html())

    def test_unflagged_project_without_stats_stays_in_the_grid(self):
        Project.objects.create(name="Small App", category=Project.Category.PERSONAL, is_featured=False)

        html = self._html()

        self.assertIn("project-card", html)
        self.assertIn("Small App", html.split('class="project-grid"')[1])

    def test_stats_do_not_promote_into_the_featured_band(self):
        """Only the flag leads the page; stats earn the card, not the position."""
        with_stats = Project.objects.create(name="Statty", category=Project.Category.PERSONAL)
        ProjectStat.objects.create(project=with_stats, label="Users", value="8M+")
        Project.objects.create(name="Flagged", category=Project.Category.PERSONAL, is_featured=True)

        html = self._html()

        self.assertLess(html.index("Flagged"), html.index("Statty"))

    def test_uses_featured_card_property(self):
        plain = Project.objects.create(name="Plain")
        flagged = Project.objects.create(name="Flagged", is_featured=True)
        statty = Project.objects.create(name="Statty")
        ProjectStat.objects.create(project=statty, label="Users", value="8M+")

        self.assertFalse(plain.uses_featured_card)
        self.assertTrue(flagged.uses_featured_card)
        self.assertTrue(statty.uses_featured_card)
