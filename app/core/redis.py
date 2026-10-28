from redis.asyncio import Redis, ConnectionPool

from app.core.config import settings

_pool: ConnectionPool | None = None


def get_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def get_redis() -> Redis:
    client = Redis(connection_pool=get_redis_pool())
    try:
        yield client
    finally:
        await client.aclose()


async def close_redis_pool() -> None:
    global _pool
    if _pool:
        await _pool.aclose()
        _pool = None
