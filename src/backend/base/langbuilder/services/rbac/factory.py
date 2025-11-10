"""Factory for creating RBAC service instances."""

from typing import TYPE_CHECKING

from typing_extensions import override

from langbuilder.services.factory import ServiceFactory
from langbuilder.services.rbac.service import RBACService

if TYPE_CHECKING:
    from langbuilder.services.database.service import DatabaseService


class RBACServiceFactory(ServiceFactory):
    """Factory for creating RBACService instances with proper dependencies."""

    name = "rbac_service"

    def __init__(self) -> None:
        """Initialize the factory with RBACService class."""
        super().__init__(RBACService)

    @override
    def create(self, database_service: "DatabaseService") -> RBACService:
        """
        Create RBACService instance with database dependency.

        Args:
            database_service: DatabaseService instance for database operations

        Returns:
            RBACService: Configured RBAC service instance
        """
        return RBACService(database_service)
