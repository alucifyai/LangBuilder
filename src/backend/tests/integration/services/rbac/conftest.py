"""Pytest configuration for RBAC integration tests.

These tests use async_session directly and don't require the full app startup.
"""

import pytest


@pytest.fixture(autouse=True)
def _start_app():
    """Override parent autouse fixture to avoid app startup.

    RBAC integration tests use async_session directly and don't need
    the full FastAPI app to be initialized.
    """
