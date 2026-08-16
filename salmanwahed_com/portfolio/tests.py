from smtplib import SMTPException
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from portfolio.forms import ContactForm
from portfolio.models import AppPrivacyPolicy, Project, ProjectImage, ProjectStat, Tag
from portfolio.views import ContactView, ProjectListView

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


@override_settings(CACHES=LOCMEM_CACHE)
class ProjectListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.professional = Project.objects.create(
            name="TallyKhata",
            category=Project.Category.PROFESSIONAL,
            role="Senior Software Engineer",
            period="2019 — Present",
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

    def test_projects_are_split_by_category(self):
        """Professional work renders as a featured card, personal work as a grid card.

        Asserted against the rendered HTML rather than response.context: this
        view is wrapped in cache_page, and the test client's context capture is
        not dependable through that decorator once a full suite has run.
        """
        response = self.client.get(reverse("portfolio:portfolio_view"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Professional work", html)
        self.assertIn("Open source &amp; personal apps", html)

        featured = html.split('class="project-grid"')[0]
        grid = html.split('class="project-grid"')[1]

        self.assertIn("TallyKhata", featured)
        self.assertNotIn("TallyKhata", grid)
        self.assertIn("SadaSidhe", grid)
        self.assertNotIn("SadaSidhe", featured)

    def test_context_exposes_both_project_groups(self):
        """The split itself, checked on the view rather than through the client."""
        view = ProjectListView()
        view.request = RequestFactory().get("/portfolio/")
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        self.assertEqual(list(context["professional_projects"]), [self.professional])
        self.assertEqual(list(context["personal_projects"]), [self.personal])
        self.assertEqual(context["active"], "projects")

    def test_featured_card_shows_badge_role_and_stats(self):
        response = self.client.get(reverse("portfolio:portfolio_view"))

        self.assertContains(response, "Featured")
        self.assertContains(response, "Senior Software Engineer")
        self.assertContains(response, "8M+")
        self.assertContains(response, "Users")

    def test_personal_project_appears_in_grid(self):
        response = self.client.get(reverse("portfolio:portfolio_view"))

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


@override_settings(CACHES=LOCMEM_CACHE)
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


@override_settings(CACHES=LOCMEM_CACHE)
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
