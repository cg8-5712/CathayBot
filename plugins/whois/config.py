"""
Whois 插件配置
"""

from pathlib import Path
from pydantic import BaseModel
import yaml


class Config(BaseModel):
    """Whois 插件配置"""

    enabled: bool = True
    timeout: int = 10  # 查询超时时间（秒）
    max_length: int = 2000  # 最大返回字符数
    default_output: str = "image"  # 默认输出模式: image / text

    @classmethod
    def load(cls, plugin_name: str) -> "Config":
        """加载插件配置"""
        config_path = Path(f"configs/plugins/{plugin_name}.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return cls(**data)
        return cls()
