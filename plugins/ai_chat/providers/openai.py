"""
OpenAI 提供商
"""

from typing import List, Dict, Optional, AsyncIterator

import httpx
from nonebot import logger

from .base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI API 提供商"""

    def __init__(self, api_key: str, model: str, api_base: Optional[str] = None):
        super().__init__(api_key, model, api_base)
        self.base_url = api_base or "https://api.openai.com/v1"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        """发送聊天请求"""
        # 构建消息列表
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)

        # 构建请求
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API 请求失败: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API 请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"OpenAI API 调用异常: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """流式聊天请求"""
        # 构建消息列表
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)

        # 构建请求
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line or line == "data: [DONE]":
                            continue

                        if line.startswith("data: "):
                            try:
                                import json

                                data = json.loads(line[6:])
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"OpenAI 流式 API 调用异常: {e}")
            raise
