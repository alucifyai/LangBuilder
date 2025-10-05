"""State management for SSO CSRF protection.

CRITICAL FIX #2 from Phase 4 Audit:
Implements state parameter verification for OIDC to prevent CSRF attacks.

HIGH PRIORITY UPDATE from Phase 5 Audit - Recommendation #3:
Updated to use Redis for production multi-server deployments.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger

try:
    import redis.asyncio as redis
except ImportError:
    redis = None  # type: ignore


class StateManager:
    """Manages SSO state parameters for CSRF protection.

    Uses Redis for distributed storage (with in-memory fallback).
    Phase 4 Audit - Critical Fix #2: OIDC state verification
    Phase 5 Audit - High Priority Fix #3: Redis support
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0", use_redis: bool = True):
        """Initialize state manager.

        Args:
            redis_url: Redis connection URL
            use_redis: Use Redis (True) or in-memory fallback (False)
        """
        self.redis_url = redis_url
        self.use_redis = use_redis and redis is not None
        self._redis_client: redis.Redis | None = None

        # In-memory fallback: {state: {user_session_id, expires_at}}
        self._states: dict[str, dict[str, Any]] = {}

        if not self.use_redis:
            logger.warning(
                "Redis not available, using in-memory state storage. "
                "This is NOT suitable for production with multiple servers."
            )

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self.use_redis and self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self._redis_client.ping()
                logger.info(f"State manager connected to Redis: {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                logger.warning("Falling back to in-memory state storage")
                self.use_redis = False
                self._redis_client = None

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

    async def generate_state(self, user_session_id: str | None = None, ttl_seconds: int = 300) -> str:
        """Generate a new state parameter.

        Args:
            user_session_id: Optional session ID to associate with state
            ttl_seconds: Time-to-live in seconds (default 5 minutes)

        Returns:
            URL-safe state token
        """
        import json

        state = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        state_data = {
            "user_session_id": user_session_id,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.use_redis and self._redis_client:
            # Store in Redis with TTL
            key = self._state_key(state)
            await self._redis_client.setex(key, ttl_seconds, json.dumps(state_data))
        else:
            # Store in-memory
            state_data["expires_at"] = expires_at  # Keep as datetime for in-memory
            state_data["created_at"] = datetime.now(timezone.utc)
            self._states[state] = state_data

        logger.debug(f"Generated state {state[:8]}... expires in {ttl_seconds}s")
        return state

    async def verify_state(self, state: str) -> bool:
        """Verify a state parameter.

        Args:
            state: State token to verify

        Returns:
            True if state is valid and not expired, False otherwise
        """
        import json

        if self.use_redis and self._redis_client:
            # Check Redis
            key = self._state_key(state)
            data = await self._redis_client.get(key)
            if not data:
                logger.warning(f"State {state[:8]}... not found")
                return False

            # Valid (TTL handled by Redis)
            logger.debug(f"State {state[:8]}... verified successfully")
            return True
        else:
            # Check in-memory
            if state not in self._states:
                logger.warning(f"State {state[:8]}... not found")
                return False

            state_data = self._states[state]
            now = datetime.now(timezone.utc)

            if state_data["expires_at"] < now:
                logger.warning(f"State {state[:8]}... expired")
                del self._states[state]
                return False

            logger.debug(f"State {state[:8]}... verified successfully")
            return True

    async def consume_state(self, state: str) -> dict[str, Any] | None:
        """Consume a state parameter (one-time use).

        Args:
            state: State token to consume

        Returns:
            State data if valid, None if invalid or expired
        """
        import json

        if not await self.verify_state(state):
            return None

        if self.use_redis and self._redis_client:
            # Get and delete from Redis
            key = self._state_key(state)
            data = await self._redis_client.get(key)
            await self._redis_client.delete(key)

            if data:
                state_data = json.loads(data)
                logger.debug(f"State {state[:8]}... consumed")
                return state_data
            return None
        else:
            # Get and delete from in-memory
            state_data = self._states.pop(state)
            logger.debug(f"State {state[:8]}... consumed")
            return state_data

    async def cleanup_expired(self) -> int:
        """Clean up expired states (for in-memory only).

        Returns:
            Number of states cleaned up

        Note: Redis handles expiration automatically via TTL
        """
        if self.use_redis:
            # Redis handles cleanup automatically
            return 0

        now = datetime.now(timezone.utc)
        expired_states = [
            state
            for state, data in self._states.items()
            if data["expires_at"] < now
        ]

        for state in expired_states:
            del self._states[state]

        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired states")

        return len(expired_states)

    def _state_key(self, state: str) -> str:
        """Generate Redis key for state."""
        return f"sso_state:{state}"


# Global state manager instance
_state_manager: StateManager | None = None


async def get_state_manager() -> StateManager:
    """Get global state manager instance.

    Returns:
        StateManager instance
    """
    global _state_manager
    if _state_manager is None:
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _state_manager = StateManager(redis_url=redis_url)
        await _state_manager.initialize()
    return _state_manager
