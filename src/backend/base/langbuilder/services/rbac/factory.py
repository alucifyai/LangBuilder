"""Factory for creating RBACService instances.

Follows the existing service factory pattern in LangBuilder.
"""

from typing_extensions import override

from langbuilder.services.factory import ServiceFactory
from langbuilder.services.rbac.service import RBACService


class RBACServiceFactory(ServiceFactory):
    """Factory for creating RBACService instances.

    Follows the singleton pattern used by other service factories.
    """

    _instance = None

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the factory with RBACService class."""
        super().__init__(RBACService)

    @override
    def create(self):
        """Create and return a new RBACService instance.

        Returns:
            RBACService: A new instance of RBACService
        """
        return RBACService()
