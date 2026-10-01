import json
import logging
from collections import deque
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger("driftguard.storage")


class StorageEngine:
    def __init__(self, redis_url: str, timeout: float = 2.0, history_limit: int = 100):
        self.redis_url = redis_url
        self.timeout = timeout
        self.history_limit = history_limit
        self.redis: aioredis.Redis | None = None
        self._is_connected = False
        self._local_health: dict[str, dict[str, Any]] = {}
        self._local_history: dict[str, deque] = {}

    async def connect(self):
        try:
            self.redis = aioredis.from_url(
                self.redis_url, socket_timeout=self.timeout, socket_connect_timeout=self.timeout, decode_responses=True
            )
            await self.redis.ping()
            self._is_connected = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            self._is_connected = False
            logger.warning(f"Redis connection failed ({e}). Operating in resilient in-memory mode.")

    async def _ensure_connection(self) -> bool:
        if self._is_connected and self.redis:
            return True
        try:
            if not self.redis:
                self.redis = aioredis.from_url(
                    self.redis_url,
                    socket_timeout=self.timeout,
                    socket_connect_timeout=self.timeout,
                    decode_responses=True,
                )
            await self.redis.ping()
            self._is_connected = True
            logger.info("Redis reconnected successfully.")
            return True
        except Exception:
            self._is_connected = False
            return False

    async def set_health(self, node: str, data: dict[str, Any]):
        # Always update in-memory state
        self._local_health[node] = dict(data)

        if await self._ensure_connection() and self.redis:
            try:
                # Store as Redis Hash
                stringified = {
                    k: json.dumps(v) if isinstance(v, (dict, list, bool)) else str(v) for k, v in data.items()
                }
                await self.redis.hset(f"driftguard:health:{node}", mapping=stringified)
            except Exception as e:
                logger.debug(f"Failed to write health to Redis: {e}")
                self._is_connected = False

    async def get_health(self, node: str) -> dict[str, Any] | None:
        # Fast read from in-memory fallback
        if node in self._local_health:
            return self._local_health[node]

        if await self._ensure_connection() and self.redis:
            try:
                raw = await self.redis.hgetall(f"driftguard:health:{node}")
                if raw:
                    parsed = {}
                    for k, v in raw.items():
                        try:
                            parsed[k] = json.loads(v)
                        except (ValueError, TypeError):
                            parsed[k] = v
                    return parsed
            except Exception as e:
                logger.debug(f"Failed to read health from Redis: {e}")
                self._is_connected = False

        return None

    async def push_history(self, node: str, data: dict[str, Any]):
        if node not in self._local_history:
            self._local_history[node] = deque(maxlen=self.history_limit)
        self._local_history[node].appendleft(dict(data))

        if await self._ensure_connection() and self.redis:
            try:
                key = f"driftguard:history:{node}"
                serialized = json.dumps(data)
                async with self.redis.pipeline(transaction=True) as pipe:
                    pipe.lpush(key, serialized)
                    pipe.ltrim(key, 0, self.history_limit - 1)
                    await pipe.execute()
            except Exception as e:
                logger.debug(f"Failed to write history to Redis: {e}")
                self._is_connected = False

    async def get_history(self, node: str, limit: int = 50) -> list[dict[str, Any]]:
        if await self._ensure_connection() and self.redis:
            try:
                key = f"driftguard:history:{node}"
                items = await self.redis.lrange(key, 0, limit - 1)
                return [json.loads(item) for item in items]
            except Exception as e:
                logger.debug(f"Failed to read history from Redis: {e}")
                self._is_connected = False

        if node in self._local_history:
            return list(self._local_history[node])[:limit]
        return []

    async def close(self):
        if self.redis:
            await self.redis.aclose()
