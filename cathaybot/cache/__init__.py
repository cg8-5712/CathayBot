"""
缓存模块

提供 Redis 缓存和内存缓存支持。
"""

from .redis import redis_client, init_redis, close_redis

__all__ = ["redis_client", "init_redis", "close_redis"]
