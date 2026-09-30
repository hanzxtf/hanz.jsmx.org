import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail_flexible_forms.models import (
    StreamFormMixin,
    AbstractSessionFormSubmission,
    AbstractSubmissionRevision,
)
from apps.core.models import BasePage
from apps.blocks.models import ContentStreamBlock
from wagtail_flexible_forms.blocks import FormFieldsBlock

logger = logging.getLogger(__name__)


class SubmissionRevision(AbstractSubmissionRevision):
    """
    SubmissionRevision is used to track changes to form submissions.
    It can be extended to add custom fields or methods if needed.
    """

    pass


class FormSubmission(AbstractSessionFormSubmission):
    """
    FormSubmission is used to store the data submitted through a form page.
    It inherits from AbstractSessionFormSubmission to leverage session management
    and can be extended with additional fields or methods as needed.
    """

    page = ParentalKey(
        "FormPage", on_delete=models.CASCADE, related_name="form_submissions"
    )

    @staticmethod
    def get_revision_class():
        return SubmissionRevision


class FormPage(StreamFormMixin, BasePage):
    """
    FormPage is a Wagtail page that allows users to create and manage forms.
    It extends StreamFormMixin to provide form functionality and uses
    BasePage for common page features.
    """

    template = "pages/form_page.html"
    landing_page_template = "pages/form_page_landing.html"
    subpage_types = []

    body = StreamField(
        ContentStreamBlock(),
        use_json_field=True,
        blank=True,
    )
    thank_you_text = models.TextField(
        blank=True, help_text="Text to display after form submission"
    )
    form_fields = StreamField(
        FormFieldsBlock(),
        use_json_field=True,
        blank=True,
    )
    to_address = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional - email address to send submissions to",
    )
    from_address = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255, blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel("body"),
        FieldPanel("form_fields"),
        FieldPanel("thank_you_text"),
        FieldPanel("to_address"),
        FieldPanel("from_address"),
        FieldPanel("subject"),
    ]

    def get_session_submission_class(self):
        return FormSubmission

    def get_session_submission(self, request):
        # Return None if the page is not yet saved (e.g., in preview)
        # to prevent a ValueError.
        if not self.pk:
            return None
        return super().get_session_submission(request)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["base_template"] = "base.html"
        return context

    def create_final_submission(self, request, delete_session=True):
        """Store the completed submission, then email it to the configured inbox."""
        submission_data = self.get_session_submission(request).get_data()
        submission = super().create_final_submission(
            request, delete_session=delete_session
        )
        self.send_mail(submission_data)
        return submission

    def send_mail(self, submission_data):
        """Notify the configured inbox about a completed submission."""
        if not self.to_address:
            return

        addresses = [x.strip() for x in self.to_address.split(",") if x.strip()]
        metadata = {"status", "user", "last_modification"}
        content = "\n".join(
            f"{key}: {value}"
            for key, value in submission_data.items()
            if key not in metadata
        )

        try:
            send_mail(
                self.subject or f"New submission: {self.title}",
                content,
                self.from_address or settings.DEFAULT_FROM_EMAIL,
                addresses,
            )
        except Exception:
            # The submission is already stored, so a mail outage (or a mail
            # server that was never configured) must not fail the visitor's
            # request. Loud in the logs, not a 500 for the person who wrote in.
            logger.exception("Could not email the submission for %r", self)
