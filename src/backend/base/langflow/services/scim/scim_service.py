"""SCIM 2.0 service implementation.

PRD Story 2.3 @AC3 - SCIM provisioning
"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from langflow.services.database.models.scim import (
    SCIMError,
    SCIMExternalMapping,
    SCIMGroupResponse,
    SCIMMember,
    SCIMMeta,
    SCIMProvisioningLog,
    SCIMProvisioningStatus,
    SCIMResourceType,
    SCIMUserResponse,
)
from langflow.services.database.models.user.model import User


class SCIMService:
    """SCIM 2.0 provisioning service.

    Implements SCIM server for user/group provisioning from IdP.
    """

    def __init__(self, workspace_id: str):
        """Initialize SCIM service.

        Args:
            workspace_id: Workspace for SCIM operations
        """
        self.workspace_id = workspace_id

    async def create_user(
        self,
        db: AsyncSession,
        user_data: dict[str, Any],
        scim_token_id: UUID,
        ip_address: str | None = None,
    ) -> SCIMUserResponse:
        """Create user from SCIM request.

        Args:
            db: Database session
            user_data: SCIM user data
            scim_token_id: Token used for authentication
            ip_address: Client IP

        Returns:
            SCIM user response

        PRD Story 2.3 @AC3 - SCIM user creation
        """
        external_id = user_data.get("externalId")
        username = user_data.get("userName")
        emails = user_data.get("emails", [])
        active = user_data.get("active", True)

        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="userName is required",
            )

        # Check if user already exists
        stmt = select(User).where(User.username == username)
        result = await db.exec(stmt)
        existing_user = result.first()

        if existing_user:
            # Check if already mapped
            stmt = select(SCIMExternalMapping).where(
                SCIMExternalMapping.external_id == external_id,
                SCIMExternalMapping.workspace_id == self.workspace_id,
            )
            result = await db.exec(stmt)
            mapping = result.first()

            if mapping:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with externalId '{external_id}' already exists",
                )

        # Create new user
        user = User(
            username=username,
            is_active=active,
            is_superuser=False,
        )

        db.add(user)
        await db.flush()  # Get user ID

        # Create external mapping
        mapping = SCIMExternalMapping(
            workspace_id=self.workspace_id,
            external_id=external_id or str(user.id),
            resource_type=SCIMResourceType.USER,
            internal_id=user.id,
            status=SCIMProvisioningStatus.ACTIVE,
            external_data=json.dumps(user_data),
        )

        db.add(mapping)

        # Log provisioning
        log = SCIMProvisioningLog(
            workspace_id=self.workspace_id,
            operation="POST",
            resource_type=SCIMResourceType.USER,
            external_id=external_id or str(user.id),
            internal_id=user.id,
            scim_token_id=scim_token_id,
            ip_address=ip_address,
            success=True,
            request_data=json.dumps(user_data),
        )

        db.add(log)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Created SCIM user: {username} (external_id: {external_id})")

        return self._user_to_scim_response(user, mapping)

    async def get_user(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> SCIMUserResponse:
        """Get user by SCIM ID.

        Args:
            db: Database session
            user_id: SCIM user ID (external ID)

        Returns:
            SCIM user response

        PRD Story 2.3 @AC3 - SCIM user retrieval
        """
        # Find mapping
        stmt = select(SCIMExternalMapping).where(
            SCIMExternalMapping.external_id == user_id,
            SCIMExternalMapping.workspace_id == self.workspace_id,
            SCIMExternalMapping.resource_type == SCIMResourceType.USER,
        )
        result = await db.exec(stmt)
        mapping = result.first()

        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found",
            )

        # Get user
        stmt = select(User).where(User.id == mapping.internal_id)
        result = await db.exec(stmt)
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found",
            )

        return self._user_to_scim_response(user, mapping)

    async def update_user(
        self,
        db: AsyncSession,
        user_id: str,
        user_data: dict[str, Any],
        scim_token_id: UUID,
        ip_address: str | None = None,
    ) -> SCIMUserResponse:
        """Update user from SCIM request.

        Args:
            db: Database session
            user_id: SCIM user ID
            user_data: SCIM user data
            scim_token_id: Token used
            ip_address: Client IP

        Returns:
            Updated SCIM user response

        PRD Story 2.3 @AC3 - SCIM user update
        """
        # Find mapping
        stmt = select(SCIMExternalMapping).where(
            SCIMExternalMapping.external_id == user_id,
            SCIMExternalMapping.workspace_id == self.workspace_id,
            SCIMExternalMapping.resource_type == SCIMResourceType.USER,
        )
        result = await db.exec(stmt)
        mapping = result.first()

        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found",
            )

        # Get user
        stmt = select(User).where(User.id == mapping.internal_id)
        result = await db.exec(stmt)
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found",
            )

        # Update user
        if "userName" in user_data:
            user.username = user_data["userName"]
        if "active" in user_data:
            user.is_active = user_data["active"]

        # Update mapping
        mapping.external_data = json.dumps(user_data)

        # Log provisioning
        log = SCIMProvisioningLog(
            workspace_id=self.workspace_id,
            operation="PUT",
            resource_type=SCIMResourceType.USER,
            external_id=user_id,
            internal_id=user.id,
            scim_token_id=scim_token_id,
            ip_address=ip_address,
            success=True,
            request_data=json.dumps(user_data),
        )

        db.add(log)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Updated SCIM user: {user.username} (external_id: {user_id})")

        return self._user_to_scim_response(user, mapping)

    async def delete_user(
        self,
        db: AsyncSession,
        user_id: str,
        scim_token_id: UUID,
        ip_address: str | None = None,
    ) -> None:
        """Delete user from SCIM request.

        Args:
            db: Database session
            user_id: SCIM user ID
            scim_token_id: Token used
            ip_address: Client IP

        PRD Story 2.3 @AC3 - SCIM user deletion
        """
        # Find mapping
        stmt = select(SCIMExternalMapping).where(
            SCIMExternalMapping.external_id == user_id,
            SCIMExternalMapping.workspace_id == self.workspace_id,
            SCIMExternalMapping.resource_type == SCIMResourceType.USER,
        )
        result = await db.exec(stmt)
        mapping = result.first()

        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found",
            )

        # Get user
        stmt = select(User).where(User.id == mapping.internal_id)
        result = await db.exec(stmt)
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found",
            )

        # Mark as deleted (soft delete)
        mapping.status = SCIMProvisioningStatus.DELETED
        user.is_active = False

        # Log provisioning
        log = SCIMProvisioningLog(
            workspace_id=self.workspace_id,
            operation="DELETE",
            resource_type=SCIMResourceType.USER,
            external_id=user_id,
            internal_id=user.id,
            scim_token_id=scim_token_id,
            ip_address=ip_address,
            success=True,
        )

        db.add(log)
        await db.commit()

        logger.info(f"Deleted SCIM user: {user.username} (external_id: {user_id})")

    async def list_users(
        self,
        db: AsyncSession,
        start_index: int = 1,
        count: int = 100,
    ) -> dict[str, Any]:
        """List users with pagination.

        Args:
            db: Database session
            start_index: Starting index (1-based)
            count: Number of results

        Returns:
            SCIM list response

        PRD Story 2.3 @AC3 - SCIM user list
        """
        # Get mappings for this workspace
        stmt = (
            select(SCIMExternalMapping)
            .where(
                SCIMExternalMapping.workspace_id == self.workspace_id,
                SCIMExternalMapping.resource_type == SCIMResourceType.USER,
                SCIMExternalMapping.status == SCIMProvisioningStatus.ACTIVE,
            )
            .offset(start_index - 1)
            .limit(count)
        )

        result = await db.exec(stmt)
        mappings = result.all()

        # Get users
        user_ids = [m.internal_id for m in mappings]
        stmt = select(User).where(User.id.in_(user_ids))
        result = await db.exec(stmt)
        users = result.all()

        # Map users to SCIM responses
        user_map = {u.id: u for u in users}
        resources = []
        for mapping in mappings:
            if mapping.internal_id in user_map:
                user = user_map[mapping.internal_id]
                resources.append(self._user_to_scim_response(user, mapping))

        # Count total
        stmt = select(SCIMExternalMapping).where(
            SCIMExternalMapping.workspace_id == self.workspace_id,
            SCIMExternalMapping.resource_type == SCIMResourceType.USER,
            SCIMExternalMapping.status == SCIMProvisioningStatus.ACTIVE,
        )
        result = await db.exec(stmt)
        total = len(result.all())

        return {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": total,
            "startIndex": start_index,
            "itemsPerPage": len(resources),
            "Resources": resources,
        }

    def _user_to_scim_response(
        self, user: User, mapping: SCIMExternalMapping
    ) -> SCIMUserResponse:
        """Convert User to SCIM response.

        Args:
            user: User object
            mapping: External mapping

        Returns:
            SCIM user response
        """
        from langflow.services.database.models.scim import SCIMEmail, SCIMName

        return SCIMUserResponse(
            id=mapping.external_id,
            externalId=mapping.external_id,
            userName=user.username,
            name=SCIMName(formatted=user.username),
            emails=[SCIMEmail(value=user.username, type="work", primary=True)],
            active=user.is_active,
            meta=SCIMMeta(
                resourceType="User",
                created=mapping.created_at,
                lastModified=mapping.updated_at,
            ),
        )

    async def patch_user(
        self,
        db: AsyncSession,
        user_id: str,
        operations: list[dict[str, Any]],
        scim_token_id: UUID,
        ip_address: str | None = None,
    ) -> SCIMUserResponse:
        """Patch user with SCIM PATCH operations.

        Args:
            db: Database session
            user_id: SCIM user ID
            operations: PATCH operations
            scim_token_id: Token used
            ip_address: Client IP

        Returns:
            Updated SCIM user response

        PRD Story 2.3 @AC3 - SCIM PATCH operation
        """
        # Find mapping
        stmt = select(SCIMExternalMapping).where(
            SCIMExternalMapping.external_id == user_id,
            SCIMExternalMapping.workspace_id == self.workspace_id,
            SCIMExternalMapping.resource_type == SCIMResourceType.USER,
        )
        result = await db.exec(stmt)
        mapping = result.first()

        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found",
            )

        # Get user
        stmt = select(User).where(User.id == mapping.internal_id)
        result = await db.exec(stmt)
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found",
            )

        # Apply PATCH operations
        for op in operations:
            op_type = op.get("op", "").lower()
            path = op.get("path", "")
            value = op.get("value")

            if op_type == "replace":
                if path == "active" or (not path and "active" in value):
                    user.is_active = value if isinstance(value, bool) else value.get("active")
                elif path == "userName" or (not path and "userName" in value):
                    user.username = value if isinstance(value, str) else value.get("userName")

        # Log provisioning
        log = SCIMProvisioningLog(
            workspace_id=self.workspace_id,
            operation="PATCH",
            resource_type=SCIMResourceType.USER,
            external_id=user_id,
            internal_id=user.id,
            scim_token_id=scim_token_id,
            ip_address=ip_address,
            success=True,
            request_data=json.dumps({"Operations": operations}),
        )

        db.add(log)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Patched SCIM user: {user.username} (external_id: {user_id})")

        return self._user_to_scim_response(user, mapping)
