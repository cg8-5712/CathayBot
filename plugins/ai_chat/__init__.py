"""
AI Chat 插件 - 智能对话

支持多 AI 提供商、分群上下文、自定义 Prompt 等高级功能
"""

import asyncio
import random
from datetime import datetime
from typing import Optional

from nonebot import on_message, on_command, get_driver, logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg

from cathaybot.cache import redis_client

from .config import Config
from .context import ContextManager
from .providers import OpenAIProvider, ClaudeProvider
from .strategy import ReplyStrategy

__plugin_meta__ = PluginMetadata(
    name="AI 对话",
    description="智能 AI 对话，支持上下文、自定义 Prompt、多提供商",
    usage="""
机器人会自动读取并回复所有消息

管理命令：
/chat clear - 清空当前会话上下文
/chat prompt <内容> - 设置当前群的自定义 Prompt (仅管理员)
    """.strip(),
    type="application",
    config=Config,
    extra={
        "author": "cg8-5712",
        "version": "1.0.0",
        "category": "娱乐",
    },
)

# 加载配置
plugin_config = Config.load("ai_chat")

# 初始化上下文管理器
context_manager = ContextManager(plugin_config)

# 初始化回复策略
reply_strategy = ReplyStrategy(plugin_config)

# 初始化 AI 提供商
ai_provider = None


def get_ai_provider():
    """获取 AI 提供商实例"""
    global ai_provider

    if ai_provider is None:
        if not plugin_config.api_key:
            raise ValueError("未配置 API Key")

        if plugin_config.provider == "openai":
            ai_provider = OpenAIProvider(
                api_key=plugin_config.api_key,
                model=plugin_config.model,
                api_base=plugin_config.api_base or None,
            )
        elif plugin_config.provider == "claude":
            ai_provider = ClaudeProvider(
                api_key=plugin_config.api_key,
                model=plugin_config.model,
                api_base=plugin_config.api_base or None,
            )
        else:
            raise ValueError(f"不支持的 AI 提供商: {plugin_config.provider}")

    return ai_provider


# ==================== 速率限制 ====================


async def check_rate_limit(user_id: str, group_id: Optional[str] = None) -> bool:
    """检查速率限制

    Returns:
        True: 允许请求, False: 超过限制
    """
    now = datetime.now()
    minute_key = now.strftime("%Y%m%d%H%M")

    # 用户速率限制
    user_key = f"ai_chat:rate:user:{user_id}:{minute_key}"
    user_count = await redis_client.incr(user_key)
    await redis_client.expire(user_key, 60)

    if user_count > plugin_config.rate_limit_per_user:
        return False

    # 群速率限制
    if group_id:
        group_key = f"ai_chat:rate:group:{group_id}:{minute_key}"
        group_count = await redis_client.incr(group_key)
        await redis_client.expire(group_key, 60)

        if group_count > plugin_config.rate_limit_per_group:
            return False

    return True


# ==================== 冷却时间 ====================


async def is_in_cooldown(conv_id: str, user_id: str) -> bool:
    """检查是否在冷却中（仅检查，不设置）

    Returns:
        True: 冷却中, False: 可以回复
    """
    if not plugin_config.enable_cooldown:
        return False

    # 检查群聊冷却
    group_key = f"ai_chat:cooldown:group:{conv_id}"
    if await redis_client.exists(group_key):
        return True

    # 检查用户冷却
    user_key = f"ai_chat:cooldown:user:{user_id}"
    if await redis_client.exists(user_key):
        return True

    return False


async def set_cooldown(conv_id: str, user_id: str) -> None:
    """设置冷却时间（在决定回复后调用）"""
    if not plugin_config.enable_cooldown:
        return

    # 设置群聊冷却
    group_key = f"ai_chat:cooldown:group:{conv_id}"
    await redis_client.setex(group_key, plugin_config.cooldown_seconds, "1")

    # 设置用户冷却
    user_key = f"ai_chat:cooldown:user:{user_id}"
    await redis_client.setex(user_key, plugin_config.cooldown_per_user, "1")


# ==================== 智能跳过 ====================


def should_skip_message(message: str) -> bool:
    """判断是否应该跳过该消息

    Returns:
        True: 跳过, False: 处理
    """
    if not plugin_config.enable_smart_skip:
        return False

    message = message.strip()

    # 太短
    if len(message) < plugin_config.min_message_length:
        return True

    # 简单回应词
    simple_responses = [
        "好的", "好", "嗯", "哦", "啊", "哈哈", "呵呵", "嘿嘿",
        "ok", "OK", "好吧", "行", "可以", "👌", "👍", "😂", "😄"
    ]
    if message in simple_responses:
        return True

    # 纯表情（简单判断）
    if len(message) <= 5 and all(ord(c) > 127 for c in message):
        return True

    return False


# ==================== 概率控制 ====================


async def should_reply_with_probability(conv_id: str) -> bool:
    """概率控制回复

    Returns:
        True: 回复, False: 跳过
    """
    if not plugin_config.enable_probability_control:
        return True

    # 获取最近回复次数
    key = f"ai_chat:reply_count:{conv_id}"
    count = await redis_client.get(key)
    recent_count = int(count) if count else 0

    # 根据最近回复次数调整概率
    adjusted_prob = plugin_config.base_reply_probability * (0.8 ** recent_count)

    if random.random() < adjusted_prob:
        # 增加计数
        await redis_client.incr(key)
        await redis_client.expire(key, 3600)  # 1小时后重置
        return True

    return False


# ==================== 内容过滤 ====================


def filter_content(content: str) -> str:
    """过滤敏感词"""
    if not plugin_config.enable_content_filter:
        return content

    filtered = content
    for word in plugin_config.blocked_words:
        filtered = filtered.replace(word, "*" * len(word))

    return filtered


# ==================== 消息分段 ====================


def split_text_naturally(text: str, max_length: int = 80) -> list[str]:
    """自然地分割文本，模拟真人发送多条消息

    Args:
        text: 要分割的文本
        max_length: 每段最大长度

    Returns:
        分割后的文本列表
    """
    if len(text) <= max_length:
        return [text]

    # 分割符优先级：换行 > 句号 > 逗号 > 空格
    separators = ["\n\n", "\n", "。", "！", "？", "，", "、", " "]

    segments = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            segments.append(remaining.strip())
            break

        # 尝试在分割符处分割
        split_pos = -1
        for sep in separators:
            # 在 max_length 范围内查找最后一个分割符
            pos = remaining[:max_length].rfind(sep)
            if pos > max_length * 0.3:  # 至少要有 30% 的长度
                split_pos = pos + len(sep)
                break

        # 如果找不到合适的分割点，强制在 max_length 处分割
        if split_pos == -1:
            split_pos = max_length

        segment = remaining[:split_pos].strip()
        if segment:
            segments.append(segment)

        remaining = remaining[split_pos:].strip()

    return segments


# ==================== Prompt 处理 ====================


async def get_system_prompt(group_id: Optional[str], group_name: str, user_name: str) -> str:
    """获取系统 Prompt

    Args:
        group_id: 群号 (私聊为 None)
        group_name: 群名
        user_name: 用户名

    Returns:
        格式化后的系统 Prompt
    """
    # 优先使用分群 Prompt
    if group_id and group_id in plugin_config.group_prompts:
        prompt = plugin_config.group_prompts[group_id]
    else:
        prompt = plugin_config.system_prompt

    # 替换变量
    prompt = prompt.replace("{group_name}", group_name)
    prompt = prompt.replace("{user_name}", user_name)

    return prompt


# ==================== 触发检查 ====================


def should_trigger(event: MessageEvent, bot: Bot) -> bool:
    """判断是否应该触发 AI 回复

    Args:
        event: 消息事件
        bot: Bot 实例

    Returns:
        是否触发
    """
    # 监听所有消息
    return True


# ==================== AI 对话处理 ====================


async def handle_ai_chat(bot: Bot, event: MessageEvent, matcher: Matcher):
    """处理 AI 对话"""
    user_id = str(event.user_id)
    user_name = event.sender.nickname or user_id

    # 获取会话信息
    if isinstance(event, GroupMessageEvent):
        conv_id = str(event.group_id)
        conv_type = "group"
        try:
            group_info = await bot.get_group_info(group_id=event.group_id)
            group_name = group_info.get("group_name", "群聊")
        except Exception:
            group_name = "群聊"
    else:
        conv_id = user_id
        conv_type = "private"
        group_name = "私聊"

    # 提取消息内容
    message = event.get_message()
    plain_text = message.extract_plain_text().strip()

    # 移除 @机器人 的部分
    for seg in message:
        if seg.type == "at":
            plain_text = plain_text.replace(f"@{seg.data.get('qq', '')}", "").strip()

    if not plain_text:
        return

    # ========== 优化检查 ==========

    # 检测是否@机器人
    is_at_bot = False
    for seg in message:
        if seg.type == "at" and seg.data.get("qq") == str(bot.self_id):
            is_at_bot = True
            break

    # 1. 智能跳过简单消息（@机器人时不跳过）
    if not is_at_bot and should_skip_message(plain_text):
        logger.debug(f"跳过简单消息: {plain_text}")
        return

    # 2. 检查冷却状态（仅检查，不设置）
    cooldown_active = await is_in_cooldown(conv_id, user_id)

    # 3. 智能策略判断
    if not await reply_strategy.should_reply(
        message=plain_text,
        conv_id=conv_id,
        user_id=user_id,
        is_at=is_at_bot,
        cooldown_active=cooldown_active,
    ):
        logger.debug(f"策略判断：跳过回复")
        return

    # 4. 速率限制检查
    if not await check_rate_limit(user_id, conv_id if conv_type == "group" else None):
        await matcher.finish("请求过于频繁，请稍后再试")

    # 5. 决定回复后，设置冷却时间
    await set_cooldown(conv_id, user_id)

    # ========== 正常处理流程 ==========

    # 添加用户消息到上下文
    await context_manager.add_message(
        conv_id=conv_id,
        conv_type=conv_type,
        user_id=user_id,
        user_name=user_name,
        role="user",
        content=plain_text,
    )

    try:
        # 获取 AI 提供商
        provider = get_ai_provider()

        # 获取上下文（已包含压缩逻辑）
        context_messages = await context_manager.get_formatted_context(conv_id)

        # 获取系统 Prompt
        system_prompt = await get_system_prompt(
            conv_id if conv_type == "group" else None, group_name, user_name
        )

        # 调用 AI（普通模式）
        reply_text = await provider.chat(
            messages=context_messages,
            system_prompt=system_prompt,
            max_tokens=plugin_config.max_reply_length,
        )

        # 过滤内容
        reply_text = filter_content(reply_text)

        # 分段发送（模拟真人）
        if plugin_config.split_message and len(reply_text) > plugin_config.split_max_length:
            segments = split_text_naturally(reply_text, plugin_config.split_max_length)

            for i, segment in enumerate(segments):
                await matcher.send(segment)

                # 最后一段不需要延迟
                if i < len(segments) - 1:
                    # 随机延迟，模拟打字时间
                    delay = random.uniform(
                        plugin_config.split_delay_min, plugin_config.split_delay_max
                    )
                    await asyncio.sleep(delay)
        else:
            # 不分段，直接发送
            await matcher.send(reply_text)

        # 添加 AI 回复到上下文
        await context_manager.add_message(
            conv_id=conv_id,
            conv_type=conv_type,
            user_id=str(bot.self_id),
            user_name="AI",
            role="assistant",
            content=reply_text,
        )

    except Exception as e:
        logger.error(f"AI 对话处理失败: {e}")
        logger.debug(f"[DEBUG] 错误详情:")
        logger.debug(f"  - 会话ID: {conv_id}")
        logger.debug(f"  - 用户ID: {user_id}")
        logger.debug(f"  - 消息内容: {plain_text}")
        logger.debug(f"  - 上下文消息数: {len(context_messages) if 'context_messages' in locals() else 0}")
        if 'context_messages' in locals():
            logger.debug(f"  - 上下文内容: {context_messages}")
        if 'system_prompt' in locals():
            logger.debug(f"  - 系统提示词: {system_prompt[:200]}...")
        logger.debug(f"  - 异常类型: {type(e).__name__}")
        logger.debug(f"  - 异常详情: {str(e)}")
        import traceback
        logger.debug(f"  - 堆栈跟踪:\n{traceback.format_exc()}")
        await matcher.finish("抱歉，我遇到了一些问题，请稍后再试喵~")


# ==================== 消息监听 ====================

ai_chat_listener = on_message(priority=99, block=False)


@ai_chat_listener.handle()
async def handle_message(bot: Bot, event: MessageEvent, matcher: Matcher):
    """监听消息，判断是否触发 AI 对话"""
    if should_trigger(event, bot):
        await handle_ai_chat(bot, event, matcher)


# ==================== 命令处理 ====================

chat_cmd = on_command("chat", aliases={"聊天", "对话"}, priority=10, block=True)


@chat_cmd.handle()
async def handle_chat_command(bot: Bot, event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    """处理 /chat 命令"""
    arg_text = args.extract_plain_text().strip()

    # 清空上下文
    if arg_text in ("clear", "清空", "重置"):
        if isinstance(event, GroupMessageEvent):
            conv_id = str(event.group_id)
        else:
            conv_id = str(event.user_id)

        await context_manager.clear_context(conv_id)
        await matcher.finish("已清空当前会话的上下文")

    # 设置自定义 Prompt (仅群聊管理员)
    if arg_text.startswith(("prompt ", "提示词 ")):
        if not isinstance(event, GroupMessageEvent):
            await matcher.finish("仅支持在群聊中设置自定义 Prompt")

        # 检查权限
        try:
            member_info = await bot.get_group_member_info(
                group_id=event.group_id, user_id=event.user_id
            )
            role = member_info.get("role")
            if role not in ("admin", "owner"):
                await matcher.finish("仅群管理员可以设置自定义 Prompt")
        except Exception:
            await matcher.finish("获取权限信息失败")

        # 提取 Prompt 内容
        prompt_content = arg_text.split(maxsplit=1)[1] if " " in arg_text else ""
        if not prompt_content:
            await matcher.finish("请提供 Prompt 内容")

        # 保存到配置 (这里简化处理，实际应该持久化到配置文件或数据库)
        group_id = str(event.group_id)
        plugin_config.group_prompts[group_id] = prompt_content

        await matcher.finish(f"已设置当前群的自定义 Prompt:\n{prompt_content}")

    # 未知命令提示
    await matcher.finish("未知命令。可用命令：\n- /chat clear - 清空上下文\n- /chat prompt <内容> - 设置自定义 Prompt")


# ==================== 启动初始化 ====================

driver = get_driver()


@driver.on_startup
async def _():
    """启动时初始化"""
    try:
        # 测试 AI 提供商连接
        provider = get_ai_provider()
        logger.success(f"AI Chat 插件已加载，使用提供商: {plugin_config.provider}")
    except Exception as e:
        logger.warning(f"AI Chat 插件初始化失败: {e}")
