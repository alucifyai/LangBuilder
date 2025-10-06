"""
Infrastructure-as-Code (IaC) API Endpoints
Apply YAML/Terraform-like policies for roles and grants
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.rbac import Role, create_grant, create_role, get_role_by_name
from langflow.services.database.models.user import User
from langflow.services.deps import get_session
from langflow.services.iac import (
    YAMLGrantDefinition,
    YAMLPolicyDefinition,
    YAMLRoleDefinition,
    parse_yaml_grants,
    parse_yaml_policy,
    parse_yaml_roles,
)

router = APIRouter(prefix="/iac", tags=["Infrastructure as Code"])


class ApplyPolicyRequest(BaseModel):
    """Request to apply YAML policy"""

    yaml_content: str
    dry_run: bool = False  # If true, validate but don't apply


class ApplyPolicyResult(BaseModel):
    """Result of applying policy"""

    roles_created: int = 0
    roles_updated: int = 0
    grants_created: int = 0
    grants_skipped: int = 0
    errors: list[str] = []
    warnings: list[str] = []


class PolicySummary(BaseModel):
    """Summary of what would be applied"""

    roles: list[dict[str, Any]]
    grants: list[dict[str, Any]]


async def apply_role_definition(
    session: AsyncSession, role_def: YAMLRoleDefinition, dry_run: bool = False
) -> tuple[bool, str | None]:
    """
    Apply a single role definition
    Returns (created_or_updated, error_message)
    """
    try:
        # Check if role exists
        existing_role = await get_role_by_name(session, role_def.name)

        if existing_role:
            # Update existing role
            if not dry_run:
                existing_role.description = role_def.description or existing_role.description
                existing_role.permissions = role_def.permissions
                if role_def.allowed_scopes:
                    existing_role.allowed_scopes = role_def.allowed_scopes
                session.add(existing_role)
                await session.commit()
            return (False, None)  # Updated, not created

        # Create new role
        if not dry_run:
            await create_role(
                session=session,
                name=role_def.name,
                description=role_def.description,
                permissions=role_def.permissions,
                allowed_scopes=role_def.allowed_scopes,
                is_system_role=False,
            )
        return (True, None)  # Created

    except Exception as e:
        return (False, str(e))


async def apply_grant_definition(
    session: AsyncSession, grant_def: YAMLGrantDefinition, dry_run: bool = False
) -> tuple[bool, str | None]:
    """
    Apply a single grant definition
    Returns (created, error_message)
    """
    try:
        # Parse principal
        principal_type, principal_id = grant_def.parse_principal()

        # Resolve principal ID if it's a username/email
        if principal_type == "user":
            # Try to find user by username or email
            result = await session.exec(
                select(User).where((User.username == principal_id) | (User.username == principal_id))
            )
            user = result.first()
            if not user:
                return (False, f"User not found: {principal_id}")
            principal_id = str(user.id)

        # Get role by name
        role = await get_role_by_name(session, grant_def.role)
        if not role:
            return (False, f"Role not found: {grant_def.role}")

        # Parse scope
        scope_type, scope_id = grant_def.scope.to_scope_tuple()

        # Parse expiration
        expires_at = None
        if grant_def.expires_at:
            try:
                expires_at = datetime.fromisoformat(grant_def.expires_at)
            except ValueError as e:
                return (False, f"Invalid expires_at format: {e}")

        # Create grant
        if not dry_run:
            try:
                await create_grant(
                    session=session,
                    principal_type=principal_type,
                    principal_id=principal_id,
                    role_id=role.id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    expires_at=expires_at,
                    justification=grant_def.justification,
                )
                return (True, None)
            except Exception as e:
                # Grant might already exist
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    return (False, None)  # Skip duplicate
                return (False, str(e))

        return (True, None)

    except Exception as e:
        return (False, str(e))


@router.post("/apply/policy", response_model=ApplyPolicyResult)
async def apply_policy(request: ApplyPolicyRequest, session: AsyncSession = Depends(get_session)):
    """
    Apply complete YAML policy (roles + grants)
    Supports dry-run mode for validation
    """
    result = ApplyPolicyResult()

    try:
        # Parse YAML
        policy = parse_yaml_policy(request.yaml_content)

        # Apply roles
        for role_def in policy.roles:
            created, error = await apply_role_definition(session, role_def, request.dry_run)
            if error:
                result.errors.append(f"Role '{role_def.name}': {error}")
            elif created:
                result.roles_created += 1
            else:
                result.roles_updated += 1

        # Apply grants
        for grant_def in policy.grants:
            created, error = await apply_grant_definition(session, grant_def, request.dry_run)
            if error:
                if error:  # Has error message
                    result.errors.append(f"Grant for '{grant_def.principal}': {error}")
                else:  # Skip duplicate
                    result.grants_skipped += 1
            elif created:
                result.grants_created += 1

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/apply/roles", response_model=ApplyPolicyResult)
async def apply_roles(request: ApplyPolicyRequest, session: AsyncSession = Depends(get_session)):
    """
    Apply roles-only YAML policy
    """
    result = ApplyPolicyResult()

    try:
        # Parse YAML
        roles = parse_yaml_roles(request.yaml_content)

        # Apply each role
        for role_def in roles:
            created, error = await apply_role_definition(session, role_def, request.dry_run)
            if error:
                result.errors.append(f"Role '{role_def.name}': {error}")
            elif created:
                result.roles_created += 1
            else:
                result.roles_updated += 1

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/apply/grants", response_model=ApplyPolicyResult)
async def apply_grants(request: ApplyPolicyRequest, session: AsyncSession = Depends(get_session)):
    """
    Apply grants-only YAML policy
    """
    result = ApplyPolicyResult()

    try:
        # Parse YAML
        grants = parse_yaml_grants(request.yaml_content)

        # Apply each grant
        for grant_def in grants:
            created, error = await apply_grant_definition(session, grant_def, request.dry_run)
            if error:
                if error:  # Has error message
                    result.errors.append(f"Grant for '{grant_def.principal}': {error}")
                else:  # Skip duplicate
                    result.grants_skipped += 1
            elif created:
                result.grants_created += 1

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/apply/file", response_model=ApplyPolicyResult)
async def apply_policy_file(
    file: UploadFile = File(...),
    dry_run: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """
    Upload and apply YAML policy file
    Supports .yaml, .yml extensions
    """
    # Validate file extension
    if not file.filename or not file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a YAML file (.yaml or .yml)",
        )

    try:
        # Read file content
        content = await file.read()
        yaml_content = content.decode("utf-8")

        # Apply policy
        return await apply_policy(
            ApplyPolicyRequest(yaml_content=yaml_content, dry_run=dry_run), session
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be valid UTF-8 text"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/validate/policy", response_model=PolicySummary)
async def validate_policy(request: ApplyPolicyRequest):
    """
    Validate and preview YAML policy without applying
    Returns what would be created/updated
    """
    try:
        policy = parse_yaml_policy(request.yaml_content)

        return PolicySummary(
            roles=[
                {
                    "name": r.name,
                    "description": r.description,
                    "permissions": r.permissions,
                    "allowed_scopes": r.allowed_scopes,
                }
                for r in policy.roles
            ],
            grants=[
                {
                    "principal": g.principal,
                    "role": g.role,
                    "scope": g.scope.dict(exclude_none=True),
                    "expires_at": g.expires_at,
                    "justification": g.justification,
                }
                for g in policy.grants
            ],
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
