"""
Admin 插件配置
"""

from cathaybot.utils.plugin_config import PluginConfig
from pydantic import Field


class Config(PluginConfig):
    """Admin 插件配置"""

    # 是否允许远程重载插件
    allow_reload: bool = Field(default=True, description="是否允许远程重载插件")

    # 是否允许广播消息
    allow_broadcast: bool = Field(default=True, description="是否允许广播消息")

    # 广播消息间隔 (秒)，防止风控
    broadcast_interval: float = Field(default=1.0, description="广播消息间隔(秒)")

    # 默认输出模式: image / text
    default_output: str = Field(default="image", description="默认输出模式")
