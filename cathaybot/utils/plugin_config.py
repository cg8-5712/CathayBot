"""
插件配置基类

为每个插件提供独立的 YAML 配置文件支持。
"""

from pathlib import Path
from typing import TypeVar, Type

import yaml
from pydantic import BaseModel, Field

T = TypeVar("T", bound="PluginConfig")


class PluginConfig(BaseModel):
    """
    插件配置基类

    每个插件可以继承此类定义自己的配置项，
    配置文件存储在 configs/plugins/<plugin_name>.yaml

    Example:
        ```python
        class MyPluginConfig(PluginConfig):
            some_option: str = "default"
            max_count: int = 100

        # 加载配置
        config = MyPluginConfig.load("my_plugin")

        # 保存配置
        config.save("my_plugin")
        ```
    """

    enabled: bool = Field(default=True, description="是否启用插件")

    @classmethod
    def load(cls: Type[T], plugin_name: str, config_dir: str = "configs/plugins") -> T:
        """
        从 YAML 文件加载插件配置

        Args:
            plugin_name: 插件名称
            config_dir: 配置目录路径

        Returns:
            插件配置实例
        """
        config_path = Path(config_dir) / f"{plugin_name}.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return cls.model_validate(data)
        return cls()

    def save(self, plugin_name: str, config_dir: str = "configs/plugins") -> None:
        """
        保存插件配置到 YAML 文件

        Args:
            plugin_name: 插件名称
            config_dir: 配置目录路径
        """
        config_path = Path(config_dir) / f"{plugin_name}.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.model_dump(exclude_none=True),
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

    @classmethod
    def ensure_config(cls: Type[T], plugin_name: str, config_dir: str = "configs/plugins") -> T:
        """
        确保配置文件存在，如果不存在则创建默认配置

        Args:
            plugin_name: 插件名称
            config_dir: 配置目录路径

        Returns:
            插件配置实例
        """
        config_path = Path(config_dir) / f"{plugin_name}.yaml"
        if not config_path.exists():
            instance = cls()
            instance.save(plugin_name, config_dir)
            return instance
        return cls.load(plugin_name, config_dir)
