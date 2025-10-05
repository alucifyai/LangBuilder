"""Infrastructure as Code (IaC) API endpoints for RBAC.

PRD Story 3.3 - Manage Roles via IaC
PRD Story 3.6 - Assign Roles via IaC (YAML/Terraform)
Phase 6: IaC Support
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import RequirePermission
from langflow.services.iac.yaml_apply_service import ApplyResult, YAMLApplyService
from langflow.services.iac.yaml_parser import RBACPolicy, YAMLParseError, YAMLParser

router = APIRouter(prefix="/iac", tags=["Infrastructure as Code"])


class ApplyPolicyRequest(BaseModel):
    """Apply policy request."""

    yaml_content: str
    dry_run: bool = False
    prune: bool = False


class ApplyPolicyResponse(BaseModel):
    """Apply policy response."""

    success: bool
    dry_run: bool
    roles_created: int
    roles_updated: int
    roles_unchanged: int
    grants_created: int
    grants_updated: int
    grants_removed: int
    errors: list[str]
    warnings: list[str]


class ValidatePolicyRequest(BaseModel):
    """Validate policy request."""

    yaml_content: str


class ValidatePolicyResponse(BaseModel):
    """Validate policy response."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    policy: RBACPolicy | None = None


class ExportPolicyResponse(BaseModel):
    """Export policy response."""

    yaml_content: str
    policy: RBACPolicy


@router.post("/apply", response_model=ApplyPolicyResponse)
async def apply_policy(
    request: ApplyPolicyRequest,
    db: DbSession,
    current_user: CurrentActiveUser,
    _perm: Annotated[None, Depends(RequirePermission("iac:apply"))] = None,
):
    """Apply RBAC policy from YAML.

    Applies role definitions and grants from YAML configuration.
    Supports dry-run mode for validation before applying changes.

    Args:
        request: Apply policy request with YAML content
        db: Database session
        current_user: Authenticated user

    Returns:
        Apply result with summary of changes

    PRD Story 3.3 @AC1 - Apply YAML policy
    PRD Story 3.6 @AC1 - Apply bindings
    """
    try:
        # Parse YAML
        policy = YAMLParser.parse(request.yaml_content)

        # Apply policy
        apply_service = YAMLApplyService(db)
        result = await apply_service.apply(
            policy=policy,
            dry_run=request.dry_run,
            prune=request.prune,
            actor_id=str(current_user.id),
        )

        return ApplyPolicyResponse(
            success=len(result.errors) == 0,
            dry_run=request.dry_run,
            roles_created=result.roles_created,
            roles_updated=result.roles_updated,
            roles_unchanged=result.roles_unchanged,
            grants_created=result.grants_created,
            grants_updated=result.grants_updated,
            grants_removed=result.grants_removed,
            errors=result.errors,
            warnings=result.warnings,
        )

    except YAMLParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid YAML: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Apply failed: {e}",
        )


@router.post("/apply-file", response_model=ApplyPolicyResponse)
async def apply_policy_file(
    db: DbSession,
    current_user: CurrentActiveUser,
    file: UploadFile = File(...),
    dry_run: bool = False,
    prune: bool = False,
    _perm: Annotated[None, Depends(RequirePermission("iac:apply"))] = None,
):
    """Apply RBAC policy from YAML file.

    Upload and apply a YAML policy file.

    Args:
        file: YAML file upload
        dry_run: Dry run mode
        prune: Prune grants not in file
        db: Database session
        current_user: Authenticated user

    Returns:
        Apply result with summary of changes

    PRD Story 3.3 @AC1 - Apply YAML policy
    """
    try:
        # Read file content
        content = await file.read()
        yaml_content = content.decode("utf-8")

        # Parse YAML
        policy = YAMLParser.parse(yaml_content)

        # Apply policy
        apply_service = YAMLApplyService(db)
        result = await apply_service.apply(
            policy=policy,
            dry_run=dry_run,
            prune=prune,
            actor_id=str(current_user.id),
        )

        return ApplyPolicyResponse(
            success=len(result.errors) == 0,
            dry_run=dry_run,
            roles_created=result.roles_created,
            roles_updated=result.roles_updated,
            roles_unchanged=result.roles_unchanged,
            grants_created=result.grants_created,
            grants_updated=result.grants_updated,
            grants_removed=result.grants_removed,
            errors=result.errors,
            warnings=result.warnings,
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded",
        )
    except YAMLParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid YAML: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Apply failed: {e}",
        )


@router.post("/validate", response_model=ValidatePolicyResponse)
async def validate_policy(
    request: ValidatePolicyRequest,
    current_user: CurrentActiveUser,
    _perm: Annotated[None, Depends(RequirePermission("iac:read"))] = None,
):
    """Validate RBAC policy YAML.

    Validates YAML syntax and policy structure without applying changes.

    Args:
        request: Validate policy request with YAML content
        current_user: Authenticated user

    Returns:
        Validation result with errors/warnings

    PRD Story 3.3 - Policy validation
    """
    try:
        # Parse YAML
        policy = YAMLParser.parse(request.yaml_content)

        # Validate policy
        errors = []
        warnings = []

        # Validate roles
        role_errors = YAMLParser.validate_roles(policy)
        errors.extend(role_errors)

        # Validate grants
        role_names = [role.name for role in policy.roles] if policy.roles else []
        grant_errors = YAMLParser.validate_grants(policy, role_names)
        errors.extend(grant_errors)

        return ValidatePolicyResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            policy=policy,
        )

    except YAMLParseError as e:
        return ValidatePolicyResponse(
            valid=False,
            errors=[str(e)],
            warnings=[],
            policy=None,
        )
    except Exception as e:
        return ValidatePolicyResponse(
            valid=False,
            errors=[f"Validation error: {e}"],
            warnings=[],
            policy=None,
        )


@router.get("/export", response_model=ExportPolicyResponse)
async def export_policy(
    db: DbSession,
    current_user: CurrentActiveUser,
    include_system_roles: bool = False,
    workspace_id: str | None = None,
    _perm: Annotated[None, Depends(RequirePermission("iac:export"))] = None,
):
    """Export current RBAC policy as YAML.

    Exports roles and grants as YAML for backup or version control.

    Args:
        db: Database session
        current_user: Authenticated user
        include_system_roles: Include system roles in export
        workspace_id: Filter grants by workspace

    Returns:
        YAML policy export

    PRD Story 3.3 - Export to YAML
    """
    from sqlmodel import select

    from langflow.services.database.models.rbac.grant import Grant
    from langflow.services.database.models.rbac.permission import Permission
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.iac.yaml_parser import (
        GrantDefinition,
        GrantScope,
        RBACPolicy,
        RoleDefinition,
        RolePermission,
    )

    try:
        # Export roles
        role_defs = []
        stmt = select(Role)
        if not include_system_roles:
            stmt = stmt.where(Role.is_system_role == False)

        roles = (await db.exec(stmt)).all()

        for role in roles:
            # Get role permissions
            perm_defs = []
            if role.permission_ids:
                # Group by resource_type
                resource_actions = {}
                for perm_id in role.permission_ids:
                    stmt = select(Permission).where(Permission.id == perm_id)
                    perm = (await db.exec(stmt)).first()
                    if perm:
                        if perm.resource_type not in resource_actions:
                            resource_actions[perm.resource_type] = []
                        resource_actions[perm.resource_type].append(perm.action)

                # Create RolePermission objects
                for resource_type, actions in resource_actions.items():
                    perm_defs.append(
                        RolePermission(
                            resource_type=resource_type,
                            actions=actions,
                        )
                    )

            role_defs.append(
                RoleDefinition(
                    name=role.name,
                    description=role.description,
                    permissions=perm_defs,
                    system_role=role.is_system_role,
                )
            )

        # Export grants
        grant_defs = []
        stmt = select(Grant)
        if workspace_id:
            # Filter by workspace (TODO: implement scope filtering)
            pass

        grants = (await db.exec(stmt)).all()

        for grant in grants:
            # Determine principal
            principal = ""
            if grant.user_id:
                # Get user email
                from langflow.services.database.models.user import User

                stmt = select(User).where(User.id == grant.user_id)
                user = (await db.exec(stmt)).first()
                if user:
                    principal = f"user:{user.username}"
            # TODO: Support group and service_account principals

            if not principal:
                continue

            # Get role name
            stmt = select(Role).where(Role.id == grant.role_id)
            role = (await db.exec(stmt)).first()
            if not role:
                continue

            # Build scope
            scope_data = grant.scope or {}
            scope = GrantScope(
                workspace=scope_data.get("workspace"),
                project=scope_data.get("project"),
                flow=scope_data.get("flow"),
                environment=scope_data.get("environment"),
            )

            grant_defs.append(
                GrantDefinition(
                    principal=principal,
                    role=role.name,
                    scope=scope,
                    expires_at=grant.expires_at.isoformat() if grant.expires_at else None,
                )
            )

        # Build policy
        policy = RBACPolicy(
            version="v1",
            roles=role_defs if role_defs else None,
            grants=grant_defs if grant_defs else None,
            metadata={
                "exported_by": current_user.username,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Convert to YAML
        yaml_content = YAMLParser.dump(policy)

        return ExportPolicyResponse(
            yaml_content=yaml_content,
            policy=policy,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {e}",
        )


@router.get("/example")
async def get_example_policy(
    current_user: CurrentActiveUser,
    _perm: Annotated[None, Depends(RequirePermission("iac:read"))] = None,
):
    """Get example RBAC policy YAML.

    Returns a complete example policy for reference.

    Args:
        current_user: Authenticated user

    Returns:
        Example YAML policy
    """
    from langflow.services.iac.yaml_parser import EXAMPLE_YAML

    return {
        "yaml_content": EXAMPLE_YAML,
        "description": "Example RBAC policy with roles and grants",
    }


# Import datetime for export endpoint
from datetime import datetime, timezone
