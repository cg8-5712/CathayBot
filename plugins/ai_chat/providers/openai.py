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
                # 记录请求信息（调试模式）
                logger.debug(f"[DEBUG] OpenAI API 请求:")
                logger.debug(f"  - URL: {self.base_url}/chat/completions")
                logger.debug(f"  - Model: {self.model}")
                logger.debug(f"  - Temperature: {payload.get('temperature')}")
                logger.debug(f"  - Max Tokens: {payload.get('max_tokens')}")
                logger.debug(f"  - 完整请求体 (payload):")
                import json
                logger.debug(json.dumps(payload, ensure_ascii=False, indent=2))
                logger.debug(f"  - Messages 详情:")
                for i, msg in enumerate(payload['messages']):
                    logger.debug(f"    [{i}] {msg['role']}: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )

                # 记录响应状态
                logger.debug(f"[DEBUG] OpenAI API 响应状态: {response.status_code}")
                logger.debug(f"[DEBUG] 响应头: {dict(response.headers)}")

                response.raise_for_status()

                # 检查响应内容
                response_text = response.text
                logger.debug(f"[DEBUG] 原始响应内容: {response_text[:1000]}")

                if not response_text:
                    logger.error(f"OpenAI API 返回空响应")
                    logger.error(f"[DEBUG] 请求 payload: {payload}")
                    raise Exception("API 返回空响应")

                # 尝试解析 JSON
                try:
                    data = response.json()
                    logger.debug(f"[DEBUG] 解析后的 JSON: {data}")
                except Exception as json_error:
                    logger.error(f"JSON 解析失败，响应内容: {response_text[:500]}")
                    logger.error(f"[DEBUG] 完整响应: {response_text}")
                    logger.error(f"[DEBUG] 请求 payload: {payload}")
                    raise Exception(f"API 返回非 JSON 格式: {json_error}")

                # 检查响应结构
                if "choices" not in data or not data["choices"]:
                    logger.error(f"API 响应格式异常: {data}")
                    logger.error(f"[DEBUG] 请求 payload: {payload}")
                    raise Exception("API 响应缺少 choices 字段")

                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API 请求失败: {e.response.status_code} - {e.response.text}")
            logger.error(f"[DEBUG] 请求 URL: {self.base_url}/chat/completions")
            logger.error(f"[DEBUG] 请求 payload: {payload}")
            logger.error(f"[DEBUG] 响应头: {dict(e.response.headers)}")
            raise Exception(f"API 请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"OpenAI API 调用异常: {e}")
            logger.error(f"[DEBUG] 请求 payload: {payload}")
            import traceback
            logger.error(f"[DEBUG] 堆栈跟踪:\n{traceback.format_exc()}")
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
