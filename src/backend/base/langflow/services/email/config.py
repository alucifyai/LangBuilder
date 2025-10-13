"""Email service configuration.

Configuration settings for SMTP email delivery using FastAPI-Mail.
Supports Gmail, SendGrid, AWS SES, and other SMTP providers.

Environment Variables:
    EMAIL_SMTP_HOST: SMTP server hostname (default: smtp.gmail.com)
    EMAIL_SMTP_PORT: SMTP server port (default: 587 for STARTTLS)
    EMAIL_SMTP_USER: SMTP authentication username
    EMAIL_SMTP_PASSWORD: SMTP authentication password
    EMAIL_FROM_EMAIL: Sender email address
    EMAIL_FROM_NAME: Sender display name (default: LangBuilder RBAC)
    EMAIL_ENABLED: Enable/disable email sending (default: True)
    EMAIL_USE_TLS: Use STARTTLS for encryption (default: True)
    EMAIL_USE_SSL: Use SSL/TLS for encryption (default: False)
    EMAIL_VALIDATE_CERTS: Validate SSL certificates (default: True)

Example Configuration:
    # Gmail
    EMAIL_SMTP_HOST=smtp.gmail.com
    EMAIL_SMTP_PORT=587
    EMAIL_SMTP_USER=your-email@gmail.com
    EMAIL_SMTP_PASSWORD=your-app-password
    EMAIL_FROM_EMAIL=noreply@langbuilder.com
    EMAIL_FROM_NAME=LangBuilder RBAC

    # SendGrid
    EMAIL_SMTP_HOST=smtp.sendgrid.net
    EMAIL_SMTP_PORT=587
    EMAIL_SMTP_USER=apikey
    EMAIL_SMTP_PASSWORD=your-sendgrid-api-key

    # AWS SES
    EMAIL_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
    EMAIL_SMTP_PORT=587
    EMAIL_SMTP_USER=your-aws-access-key
    EMAIL_SMTP_PASSWORD=your-aws-secret-key
"""


from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmailSettings(BaseSettings):
    """Email service configuration settings.

    Attributes:
        SMTP_HOST: SMTP server hostname
        SMTP_PORT: SMTP server port (typically 587 for STARTTLS, 465 for SSL)
        SMTP_USER: SMTP authentication username
        SMTP_PASSWORD: SMTP authentication password
        FROM_EMAIL: Email address to send from
        FROM_NAME: Display name for sender
        ENABLED: Whether email sending is enabled
        USE_TLS: Use STARTTLS for encryption (recommended)
        USE_SSL: Use SSL/TLS for encryption (alternative to STARTTLS)
        VALIDATE_CERTS: Whether to validate SSL certificates
        TIMEOUT: SMTP connection timeout in seconds
    """

    model_config = SettingsConfigDict(env_prefix="EMAIL_")

    SMTP_HOST: str = Field(
        default="smtp.gmail.com", description="SMTP server hostname"
    )
    SMTP_PORT: int = Field(
        default=587, description="SMTP server port (587=STARTTLS, 465=SSL)"
    )
    SMTP_USER: str | None = Field(
        default=None, description="SMTP authentication username"
    )
    SMTP_PASSWORD: str | None = Field(
        default=None, description="SMTP authentication password"
    )
    FROM_EMAIL: str = Field(
        default="noreply@langbuilder.com", description="Email address to send from"
    )
    FROM_NAME: str = Field(
        default="LangBuilder RBAC", description="Display name for sender"
    )
    ENABLED: bool = Field(default=True, description="Enable/disable email sending")
    USE_TLS: bool = Field(default=True, description="Use STARTTLS encryption")
    USE_SSL: bool = Field(default=False, description="Use SSL/TLS encryption")
    VALIDATE_CERTS: bool = Field(
        default=True, description="Validate SSL certificates"
    )
    TIMEOUT: int = Field(default=60, description="SMTP connection timeout in seconds")

    def is_configured(self) -> bool:
        """Check if email service is properly configured.

        Returns:
            True if SMTP credentials are provided, False otherwise
        """
        return bool(self.SMTP_USER and self.SMTP_PASSWORD)

    def get_connection_info(self) -> dict:
        """Get connection information for logging (without sensitive data).

        Returns:
            Dictionary with connection info (password masked)
        """
        return {
            "smtp_host": self.SMTP_HOST,
            "smtp_port": self.SMTP_PORT,
            "smtp_user": self.SMTP_USER,
            "from_email": self.FROM_EMAIL,
            "from_name": self.FROM_NAME,
            "enabled": self.ENABLED,
            "use_tls": self.USE_TLS,
            "use_ssl": self.USE_SSL,
            "configured": self.is_configured(),
        }
