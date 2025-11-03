#!/usr/bin/env python3
"""Quick script to seed RBAC data before running migrations."""
# ruff: noqa: D103, T201, EXE001

import sys

sys.path.insert(0, "src/backend/base")

import asyncio

from langbuilder.initial_setup.rbac_seed import seed_rbac_data
from langbuilder.services.database import get_db_service


async def main():
    db_service = get_db_service()
    await seed_rbac_data(db_service)
    print("✅ RBAC seed data populated successfully")


if __name__ == "__main__":
    asyncio.run(main())
