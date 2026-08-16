import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page, never_cache
from django.views.generic import DetailView, FormView, ListView, TemplateView

from .apps import PortfolioConfig
from .forms import ContactForm
from .models import AppPrivacyPolicy, Project

logger = logging.getLogger("default")

THROTTLE_WINDOW = 60 * 60  # seconds


class ProjectListView(ListView):
    model = Project
    ordering = ["-project_weight"]
    # `stats` is prefetched so the featured cards do not fire a query each.
    queryset = Project.objects.select_related("thumbnail", "banner").prefetch_related("tag", "stats")

    @method_decorator(cache_page(timeout=45 * 60, key_prefix=PortfolioConfig.name))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Split in Python rather than with two queries: the list is short and is
        # already loaded with its tags and stats prefetched.
        projects = list(context["object_list"])
        context["professional_projects"] = [p for p in projects if p.category == Project.Category.PROFESSIONAL]
        context["personal_projects"] = [p for p in projects if p.category == Project.Category.PERSONAL]
        context["active"] = "projects"
        return context


class ResumeView(TemplateView):
    template_name = "portfolio/resume.html"
    extra_context = {"active": "resume"}

    @method_decorator(cache_page(timeout=60 * 60, key_prefix=PortfolioConfig.name))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


@method_decorator(never_cache, name="dispatch")
class ContactView(FormView):
    """Contact form.

    never_cache matters here: cache_page would hand every visitor the same
    stored CSRF token, and every POST would then fail validation.
    """

    template_name = "portfolio/contact.html"
    form_class = ContactForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active"] = "contact"
        context["contact_email"] = settings.CONTACT_EMAIL
        context["contact_form_enabled"] = settings.CONTACT_FORM_ENABLED
        context.setdefault("sent", False)
        return context

    def post(self, request, *args, **kwargs):
        # The form is hidden while CONTACT_FORM_ENABLED is off, but the URL still
        # accepts POST. Refuse to process it rather than run the send path
        # against an unconfigured relay, which would only produce failed
        # deliveries and Sentry noise from bots probing the endpoint.
        if not settings.CONTACT_FORM_ENABLED:
            return self.get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def _client_ip(self):
        # nginx sets X-Real-IP from $remote_addr, so unlike the leftmost entry
        # of X-Forwarded-For it cannot be spoofed by the client. Without it,
        # REMOTE_ADDR behind the proxy would be 127.0.0.1 for everyone and the
        # per-IP limit would collapse into one shared global limit.
        return self.request.META.get("HTTP_X_REAL_IP") or self.request.META.get("REMOTE_ADDR", "")

    def _throttle_key(self):
        return f"contact-throttle:{self._client_ip()}"

    def _is_throttled(self):
        return cache.get(self._throttle_key(), 0) >= settings.CONTACT_RATE_LIMIT

    def _record_send(self):
        key = self._throttle_key()
        # Counts sends rather than attempts, so a typo in the email field does
        # not burn an allowance.
        cache.set(key, cache.get(key, 0) + 1, timeout=THROTTLE_WINDOW)

    def form_valid(self, form):
        if self._is_throttled():
            logger.warning("Contact form throttled for %s", self._client_ip())
            form.add_error(None, "Too many messages sent recently. Please try again later.")
            return self.form_invalid(form)

        data = form.cleaned_data
        body = "From: {name} <{email}>\n\n{message}".format(**data)

        try:
            # Sent from our own address so SPF/DKIM pass, with the enquirer on
            # Reply-To so hitting reply goes to them and not to ourselves.
            EmailMessage(
                subject=f"[salmanwahed.com] {data['subject']}",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],
                reply_to=[data["email"]],
            ).send(fail_silently=False)
        except Exception as ex:
            logger.exception(ex)
            form.add_error(None, "The message could not be sent. Please email me directly instead.")
            return self.form_invalid(form)

        self._record_send()
        logger.info("Contact form submitted by %s", data["email"])
        # Rendered rather than redirected so the success panel replaces the form
        # in place. A refresh cannot resubmit, because the response no longer
        # contains a populated form.
        return self.render_to_response(self.get_context_data(form=self.form_class(), sent=True))


class AppPrivacyPolicyView(DetailView):
    model = AppPrivacyPolicy
    template_name = "portfolio/app_privacy_policy.html"
    context_object_name = "policy"
    slug_field = "slug"
    slug_url_kwarg = "slug"
