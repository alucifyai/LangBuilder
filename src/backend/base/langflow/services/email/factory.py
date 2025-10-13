"""Email service factory for dependency injection.

This factory creates and configures the EmailService instance for the application.
"""

from typing_extensions import override

from langflow.services.email.config import EmailSettings
from langflow.services.email.service import EmailService
from langflow.services.factory import ServiceFactory


class EmailServiceFactory(ServiceFactory):
    """Factory for creating EmailService instances.

    The EmailService provides email notification capabilities for invitations,
    role assignments, and audit alerts.
    """

    name = "email_service"

    def __init__(self):
        """Initialize the email service factory."""
        super().__init__(EmailService)

    @override
    def create(self) -> EmailService:
        """Create and return an EmailService instance.

        Returns:
            EmailService: Configured email service instance
        """
        # Create EmailService with settings from environment
        settings = EmailSettings()
        return EmailService(settings)
