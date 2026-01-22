"""
Statistics 插件配置
"""

from cathaybot.utils.plugin_config import PluginConfig
from pydantic import Field


class Config(PluginConfig):
    """Statistics 插件配置"""

    # 是否统计消息
    track_messages: bool = Field(default=True, description="是否统计消息")

    # 是否统计命令调用
    track_commands: bool = Field(default=True, description="是否统计命令调用")

    # 是否忽略机器人消息
    ignore_bots: bool = Field(default=True, description="是否忽略机器人消息")

    # 数据保留天数 (0=永久保留)
    retention_days: int = Field(default=90, description="数据保留天数")

    # 排行榜显示数量
    top_limit: int = Field(default=10, description="排行榜显示数量")

    # 默认输出模式: image / text
    default_output: str = Field(default="image", description="默认输出模式")

    # 是否保存聊天记录到 Redis
    save_chat_history: bool = Field(default=True, description="是否保存聊天记录")

    # 每个会话保存的最大消息数
    max_messages_per_chat: int = Field(default=1000, description="每个会话保存的最大消息数")
