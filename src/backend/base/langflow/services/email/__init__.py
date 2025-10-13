"""Email service for LangBuilder.

This module provides email notification services for invitations, role assignments,
and audit alerts as part of the RBAC implementation (Task 3.10).

PRD References:
- Story 2.1 @AC4: Email notifications for invitation workflow
- Story 3.4 @AC6: Email notifications for role assignments
"""

from langflow.services.email.config import EmailSettings
from langflow.services.email.service import EmailService

__all__ = ["EmailService", "EmailSettings"]
