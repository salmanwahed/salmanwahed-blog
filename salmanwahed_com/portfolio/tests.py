from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from portfolio.forms import ContactForm
from portfolio.models import Project, ProjectStat
from portfolio.views import ProjectListView

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


@override_settings(CACHES=LOCMEM_CACHE, CONTACT_EMAIL="hello@example.com", CONTACT_RATE_LIMIT=2)
class ContactViewTests(TestCase):
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
