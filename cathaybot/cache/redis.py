"""
Redis 缓存管理

提供 Redis 连接和常用操作封装。
"""

from typing import Optional, Any
from datetime import datetime, timedelta

import redis.asyncio as redis
from nonebot import logger

from cathaybot.config import config


class RedisClient:
    """Redis 客户端封装"""

    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def prefix(self) -> str:
        return config.redis.prefix

    async def connect(self) -> None:
        """连接 Redis"""
        if not config.redis.enabled:
            logger.info("Redis 已禁用，使用内存缓存模式")
            return

        try:
            self._client = redis.from_url(
                config.redis.url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._client.ping()
            logger.info(f"Redis 连接成功: {config.redis.url}")
        except Exception as e:
            logger.warning(f"Redis 连接失败: {e}，将使用内存缓存模式")
            self._client = None

    async def close(self) -> None:
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def _key(self, key: str) -> str:
        """添加前缀"""
        return f"{self.prefix}{key}"

    # ==================== 基础操作 ====================

    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self._client:
            return None
        return await self._client.get(self._key(key))

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None,
    ) -> bool:
        """设置值"""
        if not self._client:
            return False
        await self._client.set(self._key(key), value, ex=expire)
        return True

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """设置值并指定过期时间（兼容方法）"""
        return await self.set(key, value, expire=seconds)

    async def delete(self, key: str) -> bool:
        """删除键"""
        if not self._client:
            return False
        await self._client.delete(self._key(key))
        return True

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._client:
            return False
        return await self._client.exists(self._key(key)) > 0

    # ==================== 计数器操作 ====================

    async def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not self._client:
            return 0
        return await self._client.incrby(self._key(key), amount)

    async def get_int(self, key: str) -> int:
        """获取整数值"""
        val = await self.get(key)
        return int(val) if val else 0

    # ==================== Hash 操作 ====================

    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取 Hash 字段"""
        if not self._client:
            return None
        return await self._client.hget(self._key(name), key)

    async def hset(self, name: str, key: str, value: str) -> bool:
        """设置 Hash 字段"""
        if not self._client:
            return False
        await self._client.hset(self._key(name), key, value)
        return True

    async def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        """递增 Hash 字段"""
        if not self._client:
            return 0
        return await self._client.hincrby(self._key(name), key, amount)

    async def hgetall(self, name: str) -> dict[str, str]:
        """获取所有 Hash 字段"""
        if not self._client:
            return {}
        return await self._client.hgetall(self._key(name))

    async def hdel(self, name: str, *keys: str) -> int:
        """删除 Hash 字段"""
        if not self._client:
            return 0
        return await self._client.hdel(self._key(name), *keys)

    # ==================== Sorted Set 操作 ====================

    async def zadd(self, name: str, mapping: dict[str, float]) -> int:
        """添加到有序集合"""
        if not self._client:
            return 0
        return await self._client.zadd(self._key(name), mapping)

    async def zincrby(self, name: str, amount: float, value: str) -> float:
        """递增有序集合成员分数"""
        if not self._client:
            return 0
        return await self._client.zincrby(self._key(name), amount, value)

    async def zrevrange(
        self,
        name: str,
        start: int = 0,
        end: int = -1,
        withscores: bool = False,
    ) -> list:
        """获取有序集合（按分数降序）"""
        if not self._client:
            return []
        return await self._client.zrevrange(
            self._key(name), start, end, withscores=withscores
        )

    async def zrem(self, name: str, *values: str) -> int:
        """从有序集合删除"""
        if not self._client:
            return 0
        return await self._client.zrem(self._key(name), *values)

    # ==================== List 操作 ====================

    async def lpush(self, name: str, *values: str) -> int:
        """左侧插入列表"""
        if not self._client:
            return 0
        return await self._client.lpush(self._key(name), *values)

    async def rpush(self, name: str, *values: str) -> int:
        """右侧插入列表"""
        if not self._client:
            return 0
        return await self._client.rpush(self._key(name), *values)

    async def lrange(self, name: str, start: int, end: int) -> list[str]:
        """获取列表范围"""
        if not self._client:
            return []
        return await self._client.lrange(self._key(name), start, end)

    async def llen(self, name: str) -> int:
        """获取列表长度"""
        if not self._client:
            return 0
        return await self._client.llen(self._key(name))

    async def ltrim(self, name: str, start: int, end: int) -> bool:
        """裁剪列表"""
        if not self._client:
            return False
        await self._client.ltrim(self._key(name), start, end)
        return True

    # ==================== 过期时间 ====================

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self._client:
            return False
        return await self._client.expire(self._key(key), seconds)

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        if not self._client:
            return -1
        return await self._client.ttl(self._key(key))

    # ==================== 批量操作 ====================

    async def keys(self, pattern: str) -> list[str]:
        """获取匹配的键"""
        if not self._client:
            return []
        full_pattern = self._key(pattern)
        keys = await self._client.keys(full_pattern)
        # 移除前缀返回
        prefix_len = len(self.prefix)
        return [k[prefix_len:] for k in keys]

    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配的键"""
        if not self._client:
            return 0
        keys = await self.keys(pattern)
        if not keys:
            return 0
        full_keys = [self._key(k) for k in keys]
        return await self._client.delete(*full_keys)


# 全局 Redis 客户端实例
redis_client = RedisClient()


async def init_redis() -> None:
    """初始化 Redis 连接"""
    await redis_client.connect()


async def close_redis() -> None:
    """关闭 Redis 连接"""
    await redis_client.close()
