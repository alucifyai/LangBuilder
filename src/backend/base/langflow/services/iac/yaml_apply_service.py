"""YAML apply service for RBAC Infrastructure as Code.

PRD Story 3.3 - Manage Roles via IaC
PRD Story 3.6 - Assign Roles via IaC (YAML/Terraform)
Phase 6: IaC Support
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from langflow.services.database.models.rbac.crud import create_grant, create_role, update_role
from langflow.services.database.models.rbac.grant import Grant
from langflow.services.database.models.rbac.permission import Permission
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.user import User
from langflow.services.iac.yaml_parser import (
    GrantDefinition,
    RBACPolicy,
    RoleDefinition,
    YAMLParser,
)


class YAMLApplyError(Exception):
    """YAML apply error."""

    pass


@dataclass
class ApplyResult:
    """Result of applying YAML policy."""

    roles_created: int = 0
    roles_updated: int = 0
    roles_unchanged: int = 0
    grants_created: int = 0
    grants_updated: int = 0
    grants_removed: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class YAMLApplyService:
    """Service for applying RBAC YAML policies.

    PRD Story 3.3 @AC1 - Apply YAML policy
    PRD Story 3.6 @AC1 - Apply bindings
    """

    def __init__(self, session: AsyncSession):
        """Initialize apply service.

        Args:
            session: Database session
        """
        self.session = session

    async def apply(
        self,
        policy: RBACPolicy,
        dry_run: bool = False,
        prune: bool = False,
        actor_id: str | None = None,
    ) -> ApplyResult:
        """Apply RBAC policy from YAML.

        Args:
            policy: Parsed RBAC policy
            dry_run: If True, don't make changes (validation only)
            prune: If True, remove grants not in policy
            actor_id: ID of user applying policy (for audit logging)

        Returns:
            ApplyResult with summary

        Raises:
            YAMLApplyError: If apply fails
        """
        result = ApplyResult()

        try:
            # Validate policy
            validation_errors = self._validate_policy(policy)
            if validation_errors:
                result.errors.extend(validation_errors)
                return result

            # Apply roles
            if policy.roles:
                await self._apply_roles(policy.roles, dry_run, result)

            # Apply grants
            if policy.grants:
                await self._apply_grants(policy.grants, dry_run, prune, result)

            # Commit if not dry run
            if not dry_run and not result.errors:
                await self.session.commit()
                logger.info(
                    f"Applied RBAC policy: {result.roles_created} roles created, "
                    f"{result.grants_created} grants created"
                )
            elif dry_run:
                logger.info("Dry run completed successfully (no changes made)")
            else:
                await self.session.rollback()
                logger.error(f"Apply failed with {len(result.errors)} errors")

            return result

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Apply error: {e}")
            raise YAMLApplyError(f"Apply failed: {e}")

    def _validate_policy(self, policy: RBACPolicy) -> list[str]:
        """Validate policy before applying.

        Args:
            policy: RBAC policy

        Returns:
            List of validation errors
        """
        errors = []

        # Validate roles
        role_errors = YAMLParser.validate_roles(policy)
        errors.extend(role_errors)

        # Validate grants (with role names from policy)
        role_names = [role.name for role in policy.roles] if policy.roles else []
        grant_errors = YAMLParser.validate_grants(policy, role_names)
        errors.extend(grant_errors)

        return errors

    async def _apply_roles(
        self,
        role_defs: list[RoleDefinition],
        dry_run: bool,
        result: ApplyResult,
    ) -> None:
        """Apply role definitions.

        Args:
            role_defs: Role definitions
            dry_run: Dry run mode
            result: Apply result to update
        """
        for role_def in role_defs:
            try:
                # Check if role exists
                stmt = select(Role).where(Role.name == role_def.name)
                existing_role = (await self.session.exec(stmt)).first()

                if existing_role:
                    # Update existing role
                    updated = await self._update_role_from_def(existing_role, role_def, dry_run)
                    if updated:
                        result.roles_updated += 1
                    else:
                        result.roles_unchanged += 1
                else:
                    # Create new role
                    await self._create_role_from_def(role_def, dry_run)
                    result.roles_created += 1

            except Exception as e:
                logger.error(f"Failed to apply role '{role_def.name}': {e}")
                result.errors.append(f"Role '{role_def.name}': {e}")

    async def _create_role_from_def(
        self,
        role_def: RoleDefinition,
        dry_run: bool,
    ) -> Role | None:
        """Create role from definition.

        Args:
            role_def: Role definition
            dry_run: Dry run mode

        Returns:
            Created role (or None if dry run)
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would create role '{role_def.name}'")
            return None

        # Build permissions list
        permissions = []
        for perm_def in role_def.permissions:
            # Find matching permission IDs
            for action in perm_def.actions:
                stmt = select(Permission).where(
                    Permission.resource_type == perm_def.resource_type,
                    Permission.action == action,
                )
                permission = (await self.session.exec(stmt)).first()
                if permission:
                    permissions.append(permission.id)
                else:
                    logger.warning(
                        f"Permission not found: {perm_def.resource_type}:{action}"
                    )

        # Create role
        role = await create_role(
            session=self.session,
            name=role_def.name,
            description=role_def.description or "",
            permission_ids=permissions,
            is_system_role=role_def.system_role,
        )

        logger.info(f"Created role '{role.name}' with {len(permissions)} permissions")
        return role

    async def _update_role_from_def(
        self,
        role: Role,
        role_def: RoleDefinition,
        dry_run: bool,
    ) -> bool:
        """Update role from definition.

        Args:
            role: Existing role
            role_def: Role definition
            dry_run: Dry run mode

        Returns:
            True if role was updated
        """
        # Check if update needed
        needs_update = False

        if role.description != (role_def.description or ""):
            needs_update = True

        # Build new permissions list
        new_permissions = []
        for perm_def in role_def.permissions:
            for action in perm_def.actions:
                stmt = select(Permission).where(
                    Permission.resource_type == perm_def.resource_type,
                    Permission.action == action,
                )
                permission = (await self.session.exec(stmt)).first()
                if permission:
                    new_permissions.append(permission.id)

        # Compare permissions
        current_permission_ids = {str(p) for p in role.permission_ids or []}
        new_permission_ids = {str(p) for p in new_permissions}

        if current_permission_ids != new_permission_ids:
            needs_update = True

        if not needs_update:
            logger.debug(f"Role '{role.name}' unchanged")
            return False

        if dry_run:
            logger.info(f"[DRY RUN] Would update role '{role.name}'")
            return True

        # Update role
        await update_role(
            session=self.session,
            role_id=role.id,
            description=role_def.description,
            permission_ids=new_permissions,
        )

        logger.info(f"Updated role '{role.name}'")
        return True

    async def _apply_grants(
        self,
        grant_defs: list[GrantDefinition],
        dry_run: bool,
        prune: bool,
        result: ApplyResult,
    ) -> None:
        """Apply grant definitions.

        Args:
            grant_defs: Grant definitions
            dry_run: Dry run mode
            prune: Remove grants not in definitions
            result: Apply result to update
        """
        applied_grant_ids = []

        for grant_def in grant_defs:
            try:
                # Parse principal
                principal_type, principal_id = grant_def.principal.split(":", 1)

                # Find role
                stmt = select(Role).where(Role.name == grant_def.role)
                role = (await self.session.exec(stmt)).first()
                if not role:
                    result.errors.append(f"Role '{grant_def.role}' not found")
                    continue

                # Find principal
                principal_uuid = await self._resolve_principal(principal_type, principal_id)
                if not principal_uuid:
                    result.errors.append(f"Principal '{grant_def.principal}' not found")
                    continue

                # Check if grant exists
                existing_grant = await self._find_existing_grant(
                    principal_type, principal_uuid, role.id, grant_def.scope.to_dict()
                )

                if existing_grant:
                    # Update existing grant
                    updated = await self._update_grant(existing_grant, grant_def, dry_run)
                    if updated:
                        result.grants_updated += 1
                    applied_grant_ids.append(str(existing_grant.id))
                else:
                    # Create new grant
                    new_grant = await self._create_grant_from_def(
                        principal_type, principal_uuid, role.id, grant_def, dry_run
                    )
                    result.grants_created += 1
                    if new_grant:
                        applied_grant_ids.append(str(new_grant.id))

            except Exception as e:
                logger.error(f"Failed to apply grant for '{grant_def.principal}': {e}")
                result.errors.append(f"Grant '{grant_def.principal}': {e}")

        # Prune grants not in policy
        if prune and not dry_run:
            removed = await self._prune_grants(applied_grant_ids)
            result.grants_removed = removed

    async def _resolve_principal(
        self,
        principal_type: str,
        principal_id: str,
    ) -> UUID | None:
        """Resolve principal to UUID.

        Args:
            principal_type: Principal type (user, group, service_account)
            principal_id: Principal identifier (email, name, etc.)

        Returns:
            Principal UUID or None if not found
        """
        if principal_type == "user":
            # Find user by email
            stmt = select(User).where(User.username == principal_id)
            user = (await self.session.exec(stmt)).first()
            return user.id if user else None

        elif principal_type == "group":
            # TODO: Implement group lookup when groups are implemented
            logger.warning(f"Group lookup not implemented: {principal_id}")
            return None

        elif principal_type == "service_account":
            # TODO: Implement service account lookup
            logger.warning(f"Service account lookup not implemented: {principal_id}")
            return None

        return None

    async def _find_existing_grant(
        self,
        principal_type: str,
        principal_id: UUID,
        role_id: UUID,
        scope: dict[str, str],
    ) -> Grant | None:
        """Find existing grant matching criteria.

        Args:
            principal_type: Principal type
            principal_id: Principal UUID
            role_id: Role UUID
            scope: Scope dict

        Returns:
            Existing grant or None
        """
        # Build query based on principal type
        if principal_type == "user":
            stmt = select(Grant).where(
                Grant.user_id == principal_id,
                Grant.role_id == role_id,
            )
        else:
            # TODO: Support group and service_account grants
            return None

        # Check scope match
        grants = (await self.session.exec(stmt)).all()
        for grant in grants:
            # TODO: Compare scope properly
            # For now, simple comparison
            if grant.scope == scope:
                return grant

        return None

    async def _create_grant_from_def(
        self,
        principal_type: str,
        principal_id: UUID,
        role_id: UUID,
        grant_def: GrantDefinition,
        dry_run: bool,
    ) -> Grant | None:
        """Create grant from definition.

        Args:
            principal_type: Principal type
            principal_id: Principal UUID
            role_id: Role UUID
            grant_def: Grant definition
            dry_run: Dry run mode

        Returns:
            Created grant (or None if dry run)
        """
        if dry_run:
            logger.info(
                f"[DRY RUN] Would create grant for '{grant_def.principal}' "
                f"with role '{grant_def.role}'"
            )
            return None

        # Parse expiration
        expires_at = None
        if grant_def.expires_at:
            expires_at = datetime.fromisoformat(grant_def.expires_at.replace("Z", "+00:00"))

        # Create grant
        grant_data = {
            "role_id": role_id,
            "scope": grant_def.scope.to_dict(),
            "expires_at": expires_at,
        }

        if principal_type == "user":
            grant_data["user_id"] = principal_id

        grant = await create_grant(session=self.session, **grant_data)

        logger.info(
            f"Created grant for '{grant_def.principal}' with role '{grant_def.role}'"
        )
        return grant

    async def _update_grant(
        self,
        grant: Grant,
        grant_def: GrantDefinition,
        dry_run: bool,
    ) -> bool:
        """Update grant from definition.

        Args:
            grant: Existing grant
            grant_def: Grant definition
            dry_run: Dry run mode

        Returns:
            True if grant was updated
        """
        # Check if update needed
        needs_update = False

        # Check expiration
        new_expires_at = None
        if grant_def.expires_at:
            new_expires_at = datetime.fromisoformat(grant_def.expires_at.replace("Z", "+00:00"))

        if grant.expires_at != new_expires_at:
            needs_update = True

        if not needs_update:
            return False

        if dry_run:
            logger.info(f"[DRY RUN] Would update grant {grant.id}")
            return True

        # Update grant
        grant.expires_at = new_expires_at
        self.session.add(grant)

        logger.info(f"Updated grant {grant.id}")
        return True

    async def _prune_grants(self, keep_grant_ids: list[str]) -> int:
        """Remove grants not in keep list.

        Args:
            keep_grant_ids: Grant IDs to keep

        Returns:
            Number of grants removed
        """
        # Get all grants
        stmt = select(Grant)
        all_grants = (await self.session.exec(stmt)).all()

        # Find grants to remove
        removed = 0
        for grant in all_grants:
            if str(grant.id) not in keep_grant_ids:
                await self.session.delete(grant)
                removed += 1
                logger.info(f"Pruned grant {grant.id}")

        return removed


# Import Pydantic BaseModel for ApplyResult
from pydantic import BaseModel
