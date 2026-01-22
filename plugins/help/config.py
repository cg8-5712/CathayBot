"""
Help 插件配置
"""

from cathaybot.utils.plugin_config import PluginConfig
from pydantic import Field


class Config(PluginConfig):
    """Help 插件配置"""

    # 每页显示的插件数量
    page_size: int = Field(default=10, description="每页显示的插件数量")

    # 是否显示隐藏插件
    show_hidden: bool = Field(default=False, description="是否显示隐藏插件")

    # 默认输出模式: image / text
    default_output: str = Field(default="image", description="默认输出模式")
