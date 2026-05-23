from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AppPrivacyPolicy, Project

DUMMY_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


class ProjectModelTest(TestCase):
    def test_str(self):
        project = Project.objects.create(name='My App')
        self.assertEqual(str(project), 'My App')

    def test_default_status_is_live(self):
        project = Project.objects.create(name='My App')
        self.assertEqual(project.status, Project.Status.LIVE)

    def test_default_type_is_mobile_app(self):
        project = Project.objects.create(name='My App')
        self.assertEqual(project.project_type, Project.ProjectType.MOBILE_APP)


@override_settings(CACHES=DUMMY_CACHE)
class ProjectListViewTest(TestCase):
    def setUp(self):
        Project.objects.create(name='Low Weight App', project_weight=10)
        Project.objects.create(name='High Weight App', project_weight=20)

    def test_returns_200(self):
        response = self.client.get(reverse('portfolio:portfolio_view'))
        self.assertEqual(response.status_code, 200)

    def test_ordered_by_weight_descending(self):
        response = self.client.get(reverse('portfolio:portfolio_view'))
        projects = list(response.context['object_list'])
        self.assertEqual(projects[0].name, 'High Weight App')
        self.assertEqual(projects[1].name, 'Low Weight App')


class AppPrivacyPolicyViewTest(TestCase):
    def setUp(self):
        self.policy = AppPrivacyPolicy.objects.create(
            name='My App Privacy Policy',
            slug='my-app',
            body='<p>Policy content here.</p>'
        )

    def test_returns_200(self):
        response = self.client.get(reverse('portfolio:app_privacy_policy', args=['my-app']))
        self.assertEqual(response.status_code, 200)

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse('portfolio:app_privacy_policy', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)

    def test_correct_policy_in_context(self):
        response = self.client.get(reverse('portfolio:app_privacy_policy', args=['my-app']))
        self.assertEqual(response.context['policy'], self.policy)
