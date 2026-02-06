"""
Claude 提供商
"""

from typing import List, Dict, Optional, AsyncIterator

import httpx
from nonebot import logger

from .base import AIProvider


class ClaudeProvider(AIProvider):
    """Anthropic Claude API 提供商"""

    def __init__(self, api_key: str, model: str, api_base: Optional[str] = None):
        super().__init__(api_key, model, api_base)
        self.base_url = api_base or "https://api.anthropic.com/v1"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """发送聊天请求"""
        # 构建请求
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]
        except httpx.HTTPStatusError as e:
            logger.error(f"Claude API 请求失败: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API 请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Claude API 调用异常: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """流式聊天请求"""
        # 构建请求
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue

                        try:
                            import json

                            data = json.loads(line[6:])
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Claude 流式 API 调用异常: {e}")
            raise
