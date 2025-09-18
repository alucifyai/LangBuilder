"""SCIM (System for Cross-domain Identity Management) provisioning service.

This module provides automated user and group lifecycle management following
SCIM 2.0 protocol and LangBuilder service patterns.
"""

# NO future annotations per Phase 1 requirements
from typing import TYPE_CHECKING

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, EmailStr
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.base import Service
from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.sso_configuration import SSOConfiguration
    from langflow.services.database.models.rbac.user_group import UserGroup, UserGroupMembership
    from langflow.services.database.models.user.model import User


class SCIMResourceType(str, Enum):
    """SCIM resource types."""

    USER = "User"
    GROUP = "Group"


class SCIMOperationType(str, Enum):
    """SCIM operation types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"


class SCIMUserStatus(str, Enum):
    """SCIM user status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass
class SCIMName:
    """SCIM name structure."""

    formatted: Optional[str] = None
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    middle_name: Optional[str] = None
    honorific_prefix: Optional[str] = None
    honorific_suffix: Optional[str] = None


@dataclass
class SCIMEmail:
    """SCIM email structure."""

    value: str
    type: str = "work"
    primary: bool = True


@dataclass
class SCIMGroup:
    """SCIM group reference."""

    value: str  # Group ID
    display: str  # Group name
    type: str = "direct"


class SCIMUserResource(BaseModel):
    """SCIM User resource representation."""

    id: Optional[str] = None
    external_id: Optional[str] = None
    user_name: str
    name: Optional[SCIMName] = None
    display_name: Optional[str] = None
    emails: List[SCIMEmail] = []
    active: bool = True
    groups: List[SCIMGroup] = []
    title: Optional[str] = None
    department: Optional[str] = None
    organization: Optional[str] = None
    manager: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class SCIMGroupResource(BaseModel):
    """SCIM Group resource representation."""

    id: Optional[str] = None
    external_id: Optional[str] = None
    display_name: str
    description: Optional[str] = None
    members: List[Dict[str, str]] = []
    meta: Optional[Dict[str, Any]] = None


@dataclass
class SCIMProvisioningEvent:
    """SCIM provisioning event for audit logging."""

    operation: SCIMOperationType
    resource_type: SCIMResourceType
    resource_id: str
    external_id: Optional[str]
    success: bool
    error_message: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class SCIMProvisioningResult(BaseModel):
    """Result of SCIM provisioning operation."""

    success: bool
    resource_id: Optional[str] = None
    external_id: Optional[str] = None
    operation: SCIMOperationType
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    changes_applied: List[str] = []
    warnings: List[str] = []


class SCIMService(Service):
    """SCIM provisioning service following LangBuilder patterns.

    Provides automated user and group lifecycle management with:
    - Real-time SSO synchronization
    - Differential updates for performance
    - Comprehensive audit logging
    - Error handling and reconciliation
    - Compliance with SCIM 2.0 protocol
    """

    name = "scim_service"

    def __init__(self):
        """Initialize SCIM service."""
        self._provisioning_stats = {
            "users_created": 0,
            "users_updated": 0,
            "users_deactivated": 0,
            "groups_created": 0,
            "groups_updated": 0,
            "errors": 0,
        }

    async def provision_user(
        self,
        session: AsyncSession,
        scim_user: SCIMUserResource,
        provider_id: UUIDstr,
        dry_run: bool = False,
    ) -> SCIMProvisioningResult:
        """Provision or update user from SCIM data.

        Args:
            session: Database session
            scim_user: SCIM user resource
            provider_id: SSO provider ID
            dry_run: If True, validate but don't persist changes

        Returns:
            Provisioning result with operation details
        """
        try:
            # Validate required fields
            if not scim_user.user_name:
                return SCIMProvisioningResult(
                    success=False,
                    operation=SCIMOperationType.CREATE,
                    error_code="missing_username",
                    error_message="Username is required for user provisioning",
                )

            if not scim_user.emails:
                return SCIMProvisioningResult(
                    success=False,
                    operation=SCIMOperationType.CREATE,
                    error_code="missing_email",
                    error_message="Email is required for user provisioning",
                )

            primary_email = next((e.value for e in scim_user.emails if e.primary), scim_user.emails[0].value)

            # Check if user exists by username or external_id
            existing_user = await self._find_existing_user(session, scim_user)

            if existing_user:
                return await self._update_user(session, existing_user, scim_user, provider_id, dry_run)
            else:
                return await self._create_user(session, scim_user, provider_id, dry_run)

        except Exception as e:
            logger.error(f"SCIM user provisioning failed: {e}")
            self._provisioning_stats["errors"] += 1

            return SCIMProvisioningResult(
                success=False,
                operation=SCIMOperationType.CREATE,
                error_code="provisioning_error",
                error_message=str(e),
            )

    async def provision_group(
        self,
        session: AsyncSession,
        scim_group: SCIMGroupResource,
        provider_id: UUIDstr,
        dry_run: bool = False,
    ) -> SCIMProvisioningResult:
        """Provision or update group from SCIM data.

        Args:
            session: Database session
            scim_group: SCIM group resource
            provider_id: SSO provider ID
            dry_run: If True, validate but don't persist changes

        Returns:
            Provisioning result with operation details
        """
        try:
            # Validate required fields
            if not scim_group.display_name:
                return SCIMProvisioningResult(
                    success=False,
                    operation=SCIMOperationType.CREATE,
                    error_code="missing_display_name",
                    error_message="Display name is required for group provisioning",
                )

            # Check if group exists
            existing_group = await self._find_existing_group(session, scim_group, provider_id)

            if existing_group:
                return await self._update_group(session, existing_group, scim_group, provider_id, dry_run)
            else:
                return await self._create_group(session, scim_group, provider_id, dry_run)

        except Exception as e:
            logger.error(f"SCIM group provisioning failed: {e}")
            self._provisioning_stats["errors"] += 1

            return SCIMProvisioningResult(
                success=False,
                operation=SCIMOperationType.CREATE,
                error_code="provisioning_error",
                error_message=str(e),
            )

    async def deprovision_user(
        self,
        session: AsyncSession,
        user_id: UUIDstr,
        external_id: Optional[str] = None,
        hard_delete: bool = False,
    ) -> SCIMProvisioningResult:
        """Deprovision user (deactivate or delete).

        Args:
            session: Database session
            user_id: Internal user ID
            external_id: External user ID from provider
            hard_delete: If True, delete user; if False, deactivate

        Returns:
            Provisioning result
        """
        try:
            from langflow.services.database.models.user.model import User

            user = await session.get(User, user_id)
            if not user:
                return SCIMProvisioningResult(
                    success=False,
                    operation=SCIMOperationType.DELETE,
                    error_code="user_not_found",
                    error_message=f"User {user_id} not found",
                )

            if hard_delete:
                # Hard delete - remove user and all associations
                await self._hard_delete_user(session, user)
                operation = SCIMOperationType.DELETE
                self._provisioning_stats["users_deactivated"] += 1
            else:
                # Soft delete - deactivate user
                user.is_active = False
                user.deactivated_at = datetime.now(timezone.utc)
                await session.commit()
                operation = SCIMOperationType.DEACTIVATE
                self._provisioning_stats["users_deactivated"] += 1

            # Log provisioning event
            await self._log_provisioning_event(
                SCIMProvisioningEvent(
                    operation=operation,
                    resource_type=SCIMResourceType.USER,
                    resource_id=str(user.id),
                    external_id=external_id,
                    success=True,
                    changes={"deactivated": True} if not hard_delete else {"deleted": True},
                )
            )

            return SCIMProvisioningResult(
                success=True,
                operation=operation,
                resource_id=str(user.id),
                external_id=external_id,
                changes_applied=["user_deactivated" if not hard_delete else "user_deleted"],
            )

        except Exception as e:
            logger.error(f"SCIM user deprovisioning failed: {e}")
            self._provisioning_stats["errors"] += 1

            return SCIMProvisioningResult(
                success=False,
                operation=SCIMOperationType.DELETE,
                error_code="deprovisioning_error",
                error_message=str(e),
            )

    async def sync_group_memberships(
        self,
        session: AsyncSession,
        group_id: UUIDstr,
        member_external_ids: List[str],
        provider_id: UUIDstr,
    ) -> SCIMProvisioningResult:
        """Synchronize group memberships from SCIM data.

        Args:
            session: Database session
            group_id: Internal group ID
            member_external_ids: List of external user IDs that should be in group
            provider_id: SSO provider ID

        Returns:
            Provisioning result with membership changes
        """
        try:
            from langflow.services.database.models.rbac.user_group import UserGroup, UserGroupMembership
            from langflow.services.database.models.user.model import User

            group = await session.get(UserGroup, group_id)
            if not group:
                return SCIMProvisioningResult(
                    success=False,
                    operation=SCIMOperationType.UPDATE,
                    error_code="group_not_found",
                    error_message=f"Group {group_id} not found",
                )

            # Get current memberships
            current_query = select(UserGroupMembership).where(
                UserGroupMembership.group_id == group_id,
                UserGroupMembership.is_active == True,
            )
            current_result = await session.exec(current_query)
            current_memberships = {str(m.user_id): m for m in current_result.all()}

            # Get users by external IDs
            target_users = {}
            for external_id in member_external_ids:
                user_query = select(User).where(User.external_id == external_id)
                user_result = await session.exec(user_query)
                user = user_result.first()
                if user:
                    target_users[str(user.id)] = user

            changes_applied = []

            # Add new memberships
            for user_id, user in target_users.items():
                if user_id not in current_memberships:
                    membership = UserGroupMembership(
                        user_id=user.id,
                        group_id=group.id,
                        is_active=True,
                    )
                    session.add(membership)
                    changes_applied.append(f"added_user_{user.username}")

            # Remove old memberships
            for user_id, membership in current_memberships.items():
                if user_id not in target_users:
                    membership.is_active = False
                    membership.removed_at = datetime.now(timezone.utc)
                    changes_applied.append(f"removed_user_{user_id}")

            await session.commit()

            # Log provisioning event
            await self._log_provisioning_event(
                SCIMProvisioningEvent(
                    operation=SCIMOperationType.UPDATE,
                    resource_type=SCIMResourceType.GROUP,
                    resource_id=str(group.id),
                    external_id=group.external_id,
                    success=True,
                    changes={"membership_changes": changes_applied},
                )
            )

            return SCIMProvisioningResult(
                success=True,
                operation=SCIMOperationType.UPDATE,
                resource_id=str(group.id),
                changes_applied=changes_applied,
            )

        except Exception as e:
            logger.error(f"SCIM group membership sync failed: {e}")
            self._provisioning_stats["errors"] += 1

            return SCIMProvisioningResult(
                success=False,
                operation=SCIMOperationType.UPDATE,
                error_code="sync_error",
                error_message=str(e),
            )

    async def reconcile_provisioning(
        self,
        session: AsyncSession,
        provider_id: UUIDstr,
        scim_users: List[SCIMUserResource],
        scim_groups: List[SCIMGroupResource],
    ) -> Dict[str, Any]:
        """Reconcile all users and groups from SCIM provider.

        Args:
            session: Database session
            provider_id: SSO provider ID
            scim_users: Complete list of users from provider
            scim_groups: Complete list of groups from provider

        Returns:
            Reconciliation summary with statistics
        """
        reconciliation_start = datetime.now(timezone.utc)
        results = {
            "users": {"processed": 0, "created": 0, "updated": 0, "errors": 0},
            "groups": {"processed": 0, "created": 0, "updated": 0, "errors": 0},
            "duration_seconds": 0,
            "timestamp": reconciliation_start.isoformat(),
        }

        try:
            # Process groups first (users may reference groups)
            for scim_group in scim_groups:
                results["groups"]["processed"] += 1

                group_result = await self.provision_group(session, scim_group, provider_id)
                if group_result.success:
                    if group_result.operation == SCIMOperationType.CREATE:
                        results["groups"]["created"] += 1
                    else:
                        results["groups"]["updated"] += 1
                else:
                    results["groups"]["errors"] += 1
                    logger.warning(f"Group provisioning failed: {group_result.error_message}")

            # Process users
            for scim_user in scim_users:
                results["users"]["processed"] += 1

                user_result = await self.provision_user(session, scim_user, provider_id)
                if user_result.success:
                    if user_result.operation == SCIMOperationType.CREATE:
                        results["users"]["created"] += 1
                    else:
                        results["users"]["updated"] += 1
                else:
                    results["users"]["errors"] += 1
                    logger.warning(f"User provisioning failed: {user_result.error_message}")

            # Calculate duration
            duration = (datetime.now(timezone.utc) - reconciliation_start).total_seconds()
            results["duration_seconds"] = duration

            logger.info(f"SCIM reconciliation completed: {results}")

            return results

        except Exception as e:
            logger.error(f"SCIM reconciliation failed: {e}")
            results["duration_seconds"] = (datetime.now(timezone.utc) - reconciliation_start).total_seconds()
            results["reconciliation_error"] = str(e)

            return results

    def get_provisioning_statistics(self) -> Dict[str, Any]:
        """Get current provisioning statistics.

        Returns:
            Dictionary with provisioning metrics
        """
        return self._provisioning_stats.copy()

    async def _find_existing_user(
        self,
        session: AsyncSession,
        scim_user: SCIMUserResource,
    ) -> Optional["User"]:
        """Find existing user by username, email, or external_id."""
        from langflow.services.database.models.user.model import User

        # Try by external_id first
        if scim_user.external_id:
            query = select(User).where(User.external_id == scim_user.external_id)
            result = await session.exec(query)
            user = result.first()
            if user:
                return user

        # Try by username
        query = select(User).where(User.username == scim_user.user_name)
        result = await session.exec(query)
        user = result.first()
        if user:
            return user

        # Try by email
        if scim_user.emails:
            primary_email = next((e.value for e in scim_user.emails if e.primary), scim_user.emails[0].value)
            query = select(User).where(User.email == primary_email)
            result = await session.exec(query)
            user = result.first()
            if user:
                return user

        return None

    async def _find_existing_group(
        self,
        session: AsyncSession,
        scim_group: SCIMGroupResource,
        provider_id: UUIDstr,
    ) -> Optional["UserGroup"]:
        """Find existing group by name or external_id."""
        from langflow.services.database.models.rbac.user_group import UserGroup

        # Try by external_id first
        if scim_group.external_id:
            query = select(UserGroup).where(
                UserGroup.external_id == scim_group.external_id,
                UserGroup.sso_provider_id == provider_id,
            )
            result = await session.exec(query)
            group = result.first()
            if group:
                return group

        # Try by display name
        query = select(UserGroup).where(
            UserGroup.name == scim_group.display_name,
            UserGroup.sso_provider_id == provider_id,
        )
        result = await session.exec(query)
        group = result.first()
        if group:
            return group

        return None

    async def _create_user(
        self,
        session: AsyncSession,
        scim_user: SCIMUserResource,
        provider_id: UUIDstr,
        dry_run: bool,
    ) -> SCIMProvisioningResult:
        """Create new user from SCIM data."""
        from langflow.services.database.models.user.model import User

        primary_email = next((e.value for e in scim_user.emails if e.primary), scim_user.emails[0].value)

        if dry_run:
            return SCIMProvisioningResult(
                success=True,
                operation=SCIMOperationType.CREATE,
                changes_applied=["user_would_be_created"],
            )

        # Create user
        user = User(
            username=scim_user.user_name,
            email=primary_email,
            external_id=scim_user.external_id,
            is_active=scim_user.active,
            is_superuser=False,
        )

        # Set name fields if available
        if scim_user.name:
            if scim_user.name.given_name:
                user.first_name = scim_user.name.given_name
            if scim_user.name.family_name:
                user.last_name = scim_user.name.family_name

        session.add(user)
        await session.commit()
        await session.refresh(user)

        self._provisioning_stats["users_created"] += 1

        # Log provisioning event
        await self._log_provisioning_event(
            SCIMProvisioningEvent(
                operation=SCIMOperationType.CREATE,
                resource_type=SCIMResourceType.USER,
                resource_id=str(user.id),
                external_id=scim_user.external_id,
                success=True,
                changes={"username": scim_user.user_name, "email": primary_email},
            )
        )

        return SCIMProvisioningResult(
            success=True,
            operation=SCIMOperationType.CREATE,
            resource_id=str(user.id),
            external_id=scim_user.external_id,
            changes_applied=["user_created"],
        )

    async def _update_user(
        self,
        session: AsyncSession,
        user: "User",
        scim_user: SCIMUserResource,
        provider_id: UUIDstr,
        dry_run: bool,
    ) -> SCIMProvisioningResult:
        """Update existing user from SCIM data."""
        changes_applied = []

        # Check for changes
        primary_email = next((e.value for e in scim_user.emails if e.primary), scim_user.emails[0].value)

        if user.email != primary_email:
            if not dry_run:
                user.email = primary_email
            changes_applied.append("email_updated")

        if user.is_active != scim_user.active:
            if not dry_run:
                user.is_active = scim_user.active
            changes_applied.append("status_updated")

        if scim_user.external_id and user.external_id != scim_user.external_id:
            if not dry_run:
                user.external_id = scim_user.external_id
            changes_applied.append("external_id_updated")

        # Update name fields if available
        if scim_user.name:
            if scim_user.name.given_name and user.first_name != scim_user.name.given_name:
                if not dry_run:
                    user.first_name = scim_user.name.given_name
                changes_applied.append("first_name_updated")

            if scim_user.name.family_name and user.last_name != scim_user.name.family_name:
                if not dry_run:
                    user.last_name = scim_user.name.family_name
                changes_applied.append("last_name_updated")

        if changes_applied and not dry_run:
            await session.commit()
            self._provisioning_stats["users_updated"] += 1

        # Log provisioning event if changes were made
        if changes_applied:
            await self._log_provisioning_event(
                SCIMProvisioningEvent(
                    operation=SCIMOperationType.UPDATE,
                    resource_type=SCIMResourceType.USER,
                    resource_id=str(user.id),
                    external_id=scim_user.external_id,
                    success=True,
                    changes={"updated_fields": changes_applied},
                )
            )

        return SCIMProvisioningResult(
            success=True,
            operation=SCIMOperationType.UPDATE,
            resource_id=str(user.id),
            external_id=scim_user.external_id,
            changes_applied=changes_applied,
        )

    async def _create_group(
        self,
        session: AsyncSession,
        scim_group: SCIMGroupResource,
        provider_id: UUIDstr,
        dry_run: bool,
    ) -> SCIMProvisioningResult:
        """Create new group from SCIM data."""
        from langflow.services.database.models.rbac.user_group import UserGroup

        if dry_run:
            return SCIMProvisioningResult(
                success=True,
                operation=SCIMOperationType.CREATE,
                changes_applied=["group_would_be_created"],
            )

        # Create group
        group = UserGroup(
            name=scim_group.display_name,
            description=scim_group.description or f"SCIM group: {scim_group.display_name}",
            external_id=scim_group.external_id,
            sso_provider_id=UUID(provider_id),
            is_active=True,
        )

        session.add(group)
        await session.commit()
        await session.refresh(group)

        self._provisioning_stats["groups_created"] += 1

        # Log provisioning event
        await self._log_provisioning_event(
            SCIMProvisioningEvent(
                operation=SCIMOperationType.CREATE,
                resource_type=SCIMResourceType.GROUP,
                resource_id=str(group.id),
                external_id=scim_group.external_id,
                success=True,
                changes={"name": scim_group.display_name},
            )
        )

        return SCIMProvisioningResult(
            success=True,
            operation=SCIMOperationType.CREATE,
            resource_id=str(group.id),
            external_id=scim_group.external_id,
            changes_applied=["group_created"],
        )

    async def _update_group(
        self,
        session: AsyncSession,
        group: "UserGroup",
        scim_group: SCIMGroupResource,
        provider_id: UUIDstr,
        dry_run: bool,
    ) -> SCIMProvisioningResult:
        """Update existing group from SCIM data."""
        changes_applied = []

        # Check for changes
        if group.name != scim_group.display_name:
            if not dry_run:
                group.name = scim_group.display_name
            changes_applied.append("name_updated")

        if scim_group.description and group.description != scim_group.description:
            if not dry_run:
                group.description = scim_group.description
            changes_applied.append("description_updated")

        if scim_group.external_id and group.external_id != scim_group.external_id:
            if not dry_run:
                group.external_id = scim_group.external_id
            changes_applied.append("external_id_updated")

        if changes_applied and not dry_run:
            await session.commit()
            self._provisioning_stats["groups_updated"] += 1

        # Log provisioning event if changes were made
        if changes_applied:
            await self._log_provisioning_event(
                SCIMProvisioningEvent(
                    operation=SCIMOperationType.UPDATE,
                    resource_type=SCIMResourceType.GROUP,
                    resource_id=str(group.id),
                    external_id=scim_group.external_id,
                    success=True,
                    changes={"updated_fields": changes_applied},
                )
            )

        return SCIMProvisioningResult(
            success=True,
            operation=SCIMOperationType.UPDATE,
            resource_id=str(group.id),
            external_id=scim_group.external_id,
            changes_applied=changes_applied,
        )

    async def _hard_delete_user(self, session: AsyncSession, user: "User") -> None:
        """Permanently delete user and all associated data."""
        from langflow.services.database.models.rbac.role_assignment import RoleAssignment
        from langflow.services.database.models.rbac.user_group import UserGroupMembership

        # Remove role assignments
        role_query = select(RoleAssignment).where(RoleAssignment.user_id == user.id)
        role_result = await session.exec(role_query)
        for assignment in role_result.all():
            await session.delete(assignment)

        # Remove group memberships
        group_query = select(UserGroupMembership).where(UserGroupMembership.user_id == user.id)
        group_result = await session.exec(group_query)
        for membership in group_result.all():
            await session.delete(membership)

        # Delete user
        await session.delete(user)
        await session.commit()

    async def _log_provisioning_event(self, event: SCIMProvisioningEvent) -> None:
        """Log SCIM provisioning event for audit trail."""
        try:
            logger.info(
                f"SCIM {event.operation}: {event.resource_type} {event.resource_id} "
                f"(external: {event.external_id}) - {'SUCCESS' if event.success else 'FAILED'}"
            )

            if event.error_message:
                logger.error(f"SCIM error: {event.error_message}")

        except Exception as e:
            logger.error(f"Failed to log SCIM provisioning event: {e}")
