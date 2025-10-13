import datetime
import secrets
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.api_key.model import ApiKey, ApiKeyCreate, ApiKeyRead, UnmaskedApiKeyRead
from langflow.services.database.models.user.model import User
from langflow.services.deps import get_settings_service, session_scope

if TYPE_CHECKING:
    from sqlmodel.sql.expression import SelectOfScalar


async def get_api_keys(session: AsyncSession, user_id: UUID) -> list[ApiKeyRead]:
    query: SelectOfScalar = select(ApiKey).where(ApiKey.user_id == user_id)
    api_keys = (await session.exec(query)).all()
    return [ApiKeyRead.model_validate(api_key) for api_key in api_keys]


async def create_api_key(session: AsyncSession, api_key_create: ApiKeyCreate, user_id: UUID) -> UnmaskedApiKeyRead:
    # Generate a random API key with 32 bytes of randomness
    generated_api_key = f"sk-{secrets.token_urlsafe(32)}"

    api_key = ApiKey(
        api_key=generated_api_key,
        name=api_key_create.name,
        user_id=user_id,
        created_at=api_key_create.created_at or datetime.datetime.now(datetime.timezone.utc),
    )

    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    unmasked = UnmaskedApiKeyRead.model_validate(api_key, from_attributes=True)
    unmasked.api_key = generated_api_key
    return unmasked


async def delete_api_key(session: AsyncSession, api_key_id: UUID) -> None:
    api_key = await session.get(ApiKey, api_key_id)
    if api_key is None:
        msg = "API Key not found"
        raise ValueError(msg)
    await session.delete(api_key)
    await session.commit()


async def check_key(session: AsyncSession, api_key: str) -> User | None:
    """Check if the API key is valid.

    Returns the User associated with the API key.
    For scope information, use check_key_with_scope() instead.
    """
    query: SelectOfScalar = select(ApiKey).options(selectinload(ApiKey.user)).where(ApiKey.api_key == api_key)
    api_key_object: ApiKey | None = (await session.exec(query)).first()
    if api_key_object is not None:
        settings_service = get_settings_service()
        if settings_service.settings.disable_track_apikey_usage is not True:
            await update_total_uses(api_key_object.id)
        return api_key_object.user
    return None


async def check_key_with_scope(session: AsyncSession, api_key: str) -> tuple[User, ApiKey] | tuple[None, None]:
    """Check if the API key is valid and return both user and ApiKey object.

    Returns a tuple of (User, ApiKey) if valid, or (None, None) if invalid.
    The ApiKey object contains scope information (workspace_id, scope_type, scope_id, scoped_permissions).

    This function is used for RBAC scope enforcement (PRD Story 4.2).

    Service Account Support:
    If the API key belongs to a service account (service_account_id is set),
    this function creates a synthetic User object representing the service account.
    """
    query: SelectOfScalar = select(ApiKey).options(selectinload(ApiKey.user)).where(ApiKey.api_key == api_key)
    api_key_object: ApiKey | None = (await session.exec(query)).first()
    if api_key_object is not None:
        settings_service = get_settings_service()
        if settings_service.settings.disable_track_apikey_usage is not True:
            await update_total_uses(api_key_object.id)

        # Handle user API keys
        if api_key_object.user_id:
            return api_key_object.user, api_key_object

        # Handle service account API keys (GAP-1 fix)
        if api_key_object.service_account_id:
            from langflow.services.database.models.rbac.service_account import ServiceAccount

            # Load service account
            sa = await session.get(ServiceAccount, api_key_object.service_account_id)
            if sa and sa.is_active:
                # Create synthetic User object for service account
                # This allows service accounts to work with existing User-based auth flow
                synthetic_user = User(
                    id=sa.id,
                    username=f"sa:{sa.name}",
                    is_active=sa.is_active,
                    is_superuser=False,  # Service accounts never have superuser privileges
                    password="",  # Not used for authentication
                )
                return synthetic_user, api_key_object

    return None, None


async def update_total_uses(api_key_id: UUID):
    """Update the total uses and last used at."""
    async with session_scope() as session:
        new_api_key = await session.get(ApiKey, api_key_id)
        if new_api_key is None:
            msg = "API Key not found"
            raise ValueError(msg)
        new_api_key.total_uses += 1
        new_api_key.last_used_at = datetime.datetime.now(datetime.timezone.utc)
        session.add(new_api_key)
        await session.commit()
