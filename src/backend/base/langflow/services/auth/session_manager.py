"""Session management for SSO authentication.

HIGH PRIORITY FIX from Phase 5 Audit - Recommendation #2:
Implements Redis-backed session management for SSO sessions.

PRD Story 2.2 - SSO Authentication
Phase 4 High Fix #4 - Session Management
"""

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger

try:
    import redis.asyncio as redis
except ImportError:
    redis = None  # type: ignore


class SessionManagerError(Exception):
    """Session management error."""

    pass


class SessionManager:
    """Manages SSO user sessions.

    Uses Redis for distributed session storage.
    Phase 5 Audit - High Priority Recommendation #2
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        session_ttl: int = 3600,
        max_sessions_per_user: int = 5,
        use_redis: bool = True,
    ):
        """Initialize session manager.

        Args:
            redis_url: Redis connection URL
            session_ttl: Session TTL in seconds (default 1 hour)
            max_sessions_per_user: Maximum concurrent sessions per user
            use_redis: Use Redis (True) or in-memory fallback (False)
        """
        self.redis_url = redis_url
        self.session_ttl = session_ttl
        self.max_sessions_per_user = max_sessions_per_user
        self.use_redis = use_redis and redis is not None

        self._redis_client: redis.Redis | None = None
        self._in_memory_sessions: dict[str, dict[str, Any]] = {}  # Fallback

        if not self.use_redis:
            logger.warning(
                "Redis not available, using in-memory session storage. "
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
                logger.info(f"Session manager connected to Redis: {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                logger.warning("Falling back to in-memory session storage")
                self.use_redis = False
                self._redis_client = None

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

    async def create_session(
        self,
        user_id: str,
        user_data: dict[str, Any],
        ttl: int | None = None,
    ) -> str:
        """Create a new session.

        Args:
            user_id: User ID
            user_data: User session data (email, name, etc.)
            ttl: Custom TTL in seconds (optional)

        Returns:
            Session ID

        Raises:
            SessionManagerError: If session creation fails
        """
        # Generate secure session ID
        session_id = secrets.token_urlsafe(32)
        session_ttl = ttl or self.session_ttl

        # Session data
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=session_ttl)).isoformat(),
            "user_data": user_data,
        }

        try:
            if self.use_redis and self._redis_client:
                # Store in Redis
                key = self._session_key(session_id)
                await self._redis_client.setex(
                    key,
                    session_ttl,
                    json.dumps(session_data),
                )

                # Track user sessions for limit enforcement
                user_sessions_key = self._user_sessions_key(user_id)
                await self._redis_client.sadd(user_sessions_key, session_id)
                await self._redis_client.expire(user_sessions_key, session_ttl)

                # Enforce max sessions per user
                await self._enforce_session_limit(user_id)

            else:
                # Fallback to in-memory
                self._in_memory_sessions[session_id] = session_data

            logger.info(f"Created session {session_id[:8]}... for user {user_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise SessionManagerError(f"Session creation failed: {e}")

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session data.

        Args:
            session_id: Session ID

        Returns:
            Session data if valid, None if not found or expired
        """
        try:
            if self.use_redis and self._redis_client:
                # Get from Redis
                key = self._session_key(session_id)
                data = await self._redis_client.get(key)
                if data:
                    session_data = json.loads(data)
                    logger.debug(f"Retrieved session {session_id[:8]}...")
                    return session_data
                return None
            else:
                # Get from in-memory
                session_data = self._in_memory_sessions.get(session_id)
                if session_data:
                    # Check expiration
                    expires_at = datetime.fromisoformat(session_data["expires_at"])
                    if datetime.now(timezone.utc) < expires_at:
                        return session_data
                    else:
                        # Expired
                        del self._in_memory_sessions[session_id]
                return None

        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        user_data: dict[str, Any],
    ) -> bool:
        """Update session data.

        Args:
            session_id: Session ID
            user_data: Updated user data

        Returns:
            True if updated, False if session not found
        """
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False

            # Update user data
            session_data["user_data"] = user_data

            if self.use_redis and self._redis_client:
                # Update in Redis (preserve TTL)
                key = self._session_key(session_id)
                ttl = await self._redis_client.ttl(key)
                if ttl > 0:
                    await self._redis_client.setex(
                        key,
                        ttl,
                        json.dumps(session_data),
                    )
                    logger.debug(f"Updated session {session_id[:8]}...")
                    return True
                return False
            else:
                # Update in-memory
                self._in_memory_sessions[session_id] = session_data
                return True

        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False

    async def renew_session(self, session_id: str, ttl: int | None = None) -> bool:
        """Renew session TTL.

        Args:
            session_id: Session ID
            ttl: New TTL in seconds (optional)

        Returns:
            True if renewed, False if session not found
        """
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False

            session_ttl = ttl or self.session_ttl
            new_expires = datetime.now(timezone.utc) + timedelta(seconds=session_ttl)
            session_data["expires_at"] = new_expires.isoformat()

            if self.use_redis and self._redis_client:
                # Renew in Redis
                key = self._session_key(session_id)
                await self._redis_client.setex(
                    key,
                    session_ttl,
                    json.dumps(session_data),
                )
                logger.debug(f"Renewed session {session_id[:8]}... for {session_ttl}s")
                return True
            else:
                # Renew in-memory
                self._in_memory_sessions[session_id] = session_data
                return True

        except Exception as e:
            logger.error(f"Failed to renew session: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        try:
            if self.use_redis and self._redis_client:
                # Delete from Redis
                key = self._session_key(session_id)
                deleted = await self._redis_client.delete(key)

                # Remove from user sessions set
                session_data = await self.get_session(session_id)
                if session_data:
                    user_id = session_data["user_id"]
                    user_sessions_key = self._user_sessions_key(user_id)
                    await self._redis_client.srem(user_sessions_key, session_id)

                logger.info(f"Deleted session {session_id[:8]}...")
                return deleted > 0
            else:
                # Delete from in-memory
                if session_id in self._in_memory_sessions:
                    del self._in_memory_sessions[session_id]
                    return True
                return False

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions deleted
        """
        try:
            if self.use_redis and self._redis_client:
                # Get user sessions
                user_sessions_key = self._user_sessions_key(user_id)
                session_ids = await self._redis_client.smembers(user_sessions_key)

                # Delete all sessions
                deleted = 0
                for session_id in session_ids:
                    if await self.delete_session(session_id):
                        deleted += 1

                # Delete user sessions set
                await self._redis_client.delete(user_sessions_key)

                logger.info(f"Deleted {deleted} sessions for user {user_id}")
                return deleted
            else:
                # Delete from in-memory
                deleted = 0
                to_delete = [
                    sid
                    for sid, data in self._in_memory_sessions.items()
                    if data.get("user_id") == user_id
                ]
                for session_id in to_delete:
                    del self._in_memory_sessions[session_id]
                    deleted += 1
                return deleted

        except Exception as e:
            logger.error(f"Failed to delete user sessions: {e}")
            return 0

    async def _enforce_session_limit(self, user_id: str) -> None:
        """Enforce maximum sessions per user.

        Deletes oldest sessions if limit exceeded.
        """
        if not self.use_redis or not self._redis_client:
            return

        try:
            user_sessions_key = self._user_sessions_key(user_id)
            session_ids = await self._redis_client.smembers(user_sessions_key)

            if len(session_ids) > self.max_sessions_per_user:
                # Get session creation times
                sessions_with_time = []
                for session_id in session_ids:
                    session_data = await self.get_session(session_id)
                    if session_data:
                        created_at = datetime.fromisoformat(session_data["created_at"])
                        sessions_with_time.append((session_id, created_at))

                # Sort by creation time (oldest first)
                sessions_with_time.sort(key=lambda x: x[1])

                # Delete oldest sessions
                to_delete = len(session_ids) - self.max_sessions_per_user
                for session_id, _ in sessions_with_time[:to_delete]:
                    await self.delete_session(session_id)
                    logger.info(f"Deleted old session {session_id[:8]}... for user {user_id} (limit exceeded)")

        except Exception as e:
            logger.error(f"Failed to enforce session limit: {e}")

    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"session:{session_id}"

    def _user_sessions_key(self, user_id: str) -> str:
        """Generate Redis key for user sessions set."""
        return f"user_sessions:{user_id}"


# Global session manager instance
_session_manager: SessionManager | None = None


async def get_session_manager() -> SessionManager:
    """Get global session manager instance.

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        session_ttl = int(os.getenv("SESSION_TTL", "3600"))
        max_sessions = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))

        _session_manager = SessionManager(
            redis_url=redis_url,
            session_ttl=session_ttl,
            max_sessions_per_user=max_sessions,
        )
        await _session_manager.initialize()

    return _session_manager
