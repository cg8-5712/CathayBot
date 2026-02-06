"""
AI 提供商基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncIterator


class AIProvider(ABC):
    """AI 提供商基类"""

    def __init__(self, api_key: str, model: str, api_base: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            system_prompt: 系统提示词
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            AI 回复内容
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """流式聊天请求

        Args:
            messages: 消息列表
            system_prompt: 系统提示词
            max_tokens: 最大 token 数
            temperature: 温度参数

        Yields:
            AI 回复的文本片段
        """
        pass
