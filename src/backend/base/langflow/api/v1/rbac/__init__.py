"""RBAC API endpoints for LangBuilder.

This module provides REST API endpoints for Role-Based Access Control (RBAC) functionality,
including workspace, project, environment, role, and permission management.
"""

from __future__ import annotations

from .projects import router as projects_router
from .roles import router as roles_router
from .workspaces import router as workspaces_router

__all__ = [
    "projects_router",
    "roles_router",
    "workspaces_router",
]
