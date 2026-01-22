"""
全局配置加载器

使用 YAML + Pydantic2 实现类型安全的配置管理。
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class BotConfig(BaseModel):
    """机器人基础配置"""

    superusers: list[str] = Field(default_factory=list, description="超级管理员 QQ 号列表")
    nickname: list[str] = Field(default_factory=lambda: ["CathayBot"], description="机器人昵称")
    command_start: list[str] = Field(default_factory=lambda: ["/", "!"], description="命令前缀")
    command_sep: list[str] = Field(default_factory=lambda: ["."], description="命令分隔符")


class DatabaseConfig(BaseModel):
    """数据库配置"""

    type: str = Field(default="sqlite", description="数据库类型: sqlite / postgresql")
    path: str = Field(default="./data/db.sqlite", description="SQLite 文件路径")
    url: Optional[str] = Field(default=None, description="PostgreSQL 连接 URL")

    # 连接池配置 (PostgreSQL)
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")

    @property
    def database_url(self) -> str:
        """获取数据库连接 URL"""
        if self.type == "postgresql" and self.url:
            return self.url
        # SQLite 使用 aiosqlite 异步驱动
        return f"sqlite+aiosqlite:///{self.path}"


class WebUIConfig(BaseModel):
    """WebUI 配置"""

    enabled: bool = Field(default=True, description="是否启用 WebUI")
    host: str = Field(default="0.0.0.0", description="监听地址")
    port: int = Field(default=8081, description="监听端口")
    secret_key: str = Field(default="change-me-in-production", description="JWT 密钥")
    token_expire_hours: int = Field(default=24, description="Token 过期时间(小时)")


class RedisConfig(BaseModel):
    """Redis 配置"""

    enabled: bool = Field(default=True, description="是否启用 Redis")
    url: str = Field(default="redis://localhost:6379/0", description="Redis 连接 URL")
    prefix: str = Field(default="cathaybot:", description="键前缀")

    # 缓存配置
    sync_interval: int = Field(default=300, description="同步到数据库的间隔(秒)")
    expire_hours: int = Field(default=24, description="统计数据过期时间(小时)")


class LoggingConfig(BaseModel):
    """日志配置"""

    level: str = Field(default="INFO", description="日志级别")
    file: str = Field(default="./logs/cathaybot.log", description="日志文件路径")
    max_size: int = Field(default=10485760, description="单个日志文件最大大小(字节)")
    backup_count: int = Field(default=5, description="日志文件备份数量")


class GlobalConfig(BaseModel):
    """全局配置"""

    bot: BotConfig = Field(default_factory=BotConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    webui: WebUIConfig = Field(default_factory=WebUIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, config_path: str = "configs/config.yaml") -> "GlobalConfig":
        """
        从 YAML 文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            GlobalConfig 实例
        """
        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return cls.model_validate(data)
        return cls()

    def save(self, config_path: str = "configs/config.yaml") -> None:
        """
        保存配置到 YAML 文件

        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.model_dump(exclude_none=True),
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )


# 全局配置单例
config = GlobalConfig.load()
