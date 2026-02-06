"""
AI Chat 智能回复策略模块
"""

import random
from datetime import datetime
from typing import Optional

from nonebot import logger

from cathaybot.cache import redis_client

from .config import Config


class ReplyStrategy:
    """回复策略管理器"""

    def __init__(self, config: Config):
        self.config = config

    async def should_reply(
        self,
        message: str,
        conv_id: str,
        user_id: str,
        is_at: bool = False,
        cooldown_active: bool = False,
    ) -> bool:
        """判断是否应该回复

        Args:
            message: 消息内容
            conv_id: 会话ID
            user_id: 用户ID
            is_at: 是否@机器人
            cooldown_active: 是否在冷却中

        Returns:
            True: 回复, False: 跳过
        """
        strategy = self.config.reply_strategy

        if strategy == "chat":
            return await self._strategy_chat(message, conv_id, is_at, cooldown_active)
        elif strategy == "importance":
            return await self._strategy_importance(message, is_at)
        elif strategy == "priority":
            return await self._strategy_priority(message, is_at, cooldown_active)
        elif strategy == "activity":
            return await self._strategy_activity(conv_id, is_at)
        elif strategy == "turns":
            return await self._strategy_turns(conv_id, is_at)
        elif strategy == "probability":
            return await self._strategy_probability(conv_id)
        else:
            return True  # 默认回复

    # ==================== 策略 0: 闲聊模式（新增）====================

    async def _strategy_chat(
        self, message: str, conv_id: str, is_at: bool, cooldown_active: bool
    ) -> bool:
        """闲聊模式策略

        核心逻辑：
        1. 群聊冷清时：主动活跃气氛，多回复
        2. 群聊热闹时：一起热闹，积极参与
        3. 避免回复简单的"哦"、"嗯"等
        4. 有趣的话题优先回复
        """
        # @机器人总是回复
        if is_at:
            return True

        # 获取群聊活跃度
        activity = await self._get_activity_level(conv_id)

        # 计算消息的"有趣度"
        interest_score = self._calculate_interest(message)

        # 根据活跃度和有趣度决定回复概率
        reply_prob = self._get_chat_probability(activity, interest_score, cooldown_active)

        should_reply = random.random() < reply_prob

        logger.debug(
            f"闲聊模式 - 活跃度: {activity}, 有趣度: {interest_score:.2f}, "
            f"概率: {reply_prob:.2f}, 回复: {should_reply}"
        )

        return should_reply

    def _calculate_interest(self, message: str) -> float:
        """计算消息的有趣度 (0.0-1.0)

        有趣的消息更容易触发回复
        """
        score = 0.5  # 基础分

        # 长消息更有趣
        if len(message) > 50:
            score += 0.2
        elif len(message) > 20:
            score += 0.1

        # 包含表情
        emoji_count = sum(1 for c in message if ord(c) > 127)
        if emoji_count > 0:
            score += min(0.2, emoji_count * 0.05)

        # 有趣的话题词（从配置读取）
        if any(word in message for word in self.config.interesting_topics):
            score += 0.2

        # 问题（但不是严肃问题）
        casual_questions = ["吗", "呢", "啊", "吧", "？", "?"]
        if any(word in message for word in casual_questions):
            score += 0.15

        # 简单回应（降低有趣度）
        simple_words = ["好的", "好", "嗯", "哦", "啊", "ok", "OK"]
        if message.strip() in simple_words:
            score = 0.0

        # 纯数字或符号
        if message.strip().isdigit() or len(message.strip()) < 2:
            score = 0.0

        return max(0.0, min(1.0, score))

    def _get_chat_probability(
        self, activity: str, interest_score: float, cooldown_active: bool
    ) -> float:
        """根据活跃度和有趣度计算回复概率

        策略：
        - 冷清时：多回复，活跃气氛
        - 热闹时：一起热闹，积极参与
        - 正常时：适度参与
        - 有趣的消息提高概率
        """
        # 基础概率（从配置读取）
        base_probs = {
            "cold": self.config.chat_prob_cold,
            "normal": self.config.chat_prob_normal,
            "active": self.config.chat_prob_active,
            "hot": self.config.chat_prob_hot,
        }

        base_prob = base_probs[activity]

        # 根据有趣度调整
        # 有趣度高的消息，概率提升
        adjusted_prob = base_prob + (interest_score - 0.5) * 0.4

        # 冷却中降低概率（但不完全阻止）
        if cooldown_active:
            adjusted_prob *= self.config.cooldown_decay

        return max(0.0, min(1.0, adjusted_prob))

    # ==================== 策略 1: 重要性评分 ====================

    async def _strategy_importance(self, message: str, is_at: bool) -> bool:
        """重要性评分策略"""
        score = self._calculate_importance(message, is_at)
        should_reply = score >= self.config.importance_threshold

        logger.debug(f"重要性评分: {score:.2f}, 阈值: {self.config.importance_threshold}, 回复: {should_reply}")
        return should_reply

    def _calculate_importance(self, message: str, is_at: bool) -> float:
        """计算消息重要性分数 (0.0-1.0)"""
        score = 0.0

        # @机器人 → 最高优先级
        if is_at:
            score += 0.5

        # 疑问词
        question_words = ["什么", "怎么", "为什么", "如何", "哪里", "哪个", "谁", "吗", "呢", "？", "?"]
        if any(word in message for word in question_words):
            score += 0.4

        # 求助词
        help_words = ["帮我", "帮忙", "请问", "能不能", "可以吗", "求", "急", "救命", "怎么办"]
        if any(word in message for word in help_words):
            score += 0.3

        # 消息长度
        if len(message) > 50:
            score += 0.3
        elif len(message) > 20:
            score += 0.2

        # 包含代码或技术词汇
        tech_keywords = ["代码", "bug", "错误", "报错", "函数", "变量", "API", "数据库"]
        if any(word in message for word in tech_keywords):
            score += 0.2

        # 简单回应（降低优先级）
        simple_words = ["好的", "好", "嗯", "哦", "啊", "哈哈", "呵呵", "ok", "OK"]
        if message.strip() in simple_words:
            score -= 0.5

        # 否定词（不需要回复）
        negative_words = ["不用", "算了", "没事", "不需要", "不用了"]
        if any(word in message for word in negative_words):
            score -= 0.3

        return max(0.0, min(1.0, score))

    # ==================== 策略 2: 优先级策略 ====================

    async def _strategy_priority(self, message: str, is_at: bool, cooldown_active: bool) -> bool:
        """优先级策略"""
        priority = self._get_message_priority(message, is_at)

        # CRITICAL (3): 总是回复，忽略冷却
        if priority >= 3:
            logger.debug(f"优先级: CRITICAL, 忽略冷却回复")
            return True

        # HIGH (2): 冷却中也回复
        if priority >= 2:
            logger.debug(f"优先级: HIGH, 回复")
            return True

        # NORMAL (1): 遵守冷却
        if priority >= 1:
            should_reply = not cooldown_active
            logger.debug(f"优先级: NORMAL, 冷却: {cooldown_active}, 回复: {should_reply}")
            return should_reply

        # LOW (0): 跳过
        logger.debug(f"优先级: LOW, 跳过")
        return False

    def _get_message_priority(self, message: str, is_at: bool) -> int:
        """获取消息优先级 (0-3)"""
        # @机器人 → CRITICAL
        if is_at:
            return 3

        # 求助类 → CRITICAL
        help_keywords = ["帮我", "救命", "急", "怎么办", "出错了", "bug", "报错"]
        if any(kw in message for kw in help_keywords):
            return 3

        # 问题类 → HIGH
        question_keywords = ["什么", "怎么", "为什么", "如何", "？", "?", "请问"]
        if any(kw in message for kw in question_keywords):
            return 2

        # 闲聊类 → NORMAL
        chat_keywords = ["今天", "最近", "觉得", "感觉", "听说"]
        if any(kw in message for kw in chat_keywords):
            return 1

        # 简单回应 → LOW
        simple_responses = ["好的", "嗯", "哦", "哈哈", "呵呵"]
        if message.strip() in simple_responses:
            return 0

        return 1  # 默认 NORMAL

    # ==================== 策略 3: 活跃度自适应 ====================

    async def _strategy_activity(self, conv_id: str, is_at: bool) -> bool:
        """活跃度自适应策略"""
        # @机器人总是回复
        if is_at:
            return True

        activity = await self._get_activity_level(conv_id)
        probabilities = {
            "cold": 0.8,    # 冷清时多回复
            "normal": 0.5,  # 正常时适度回复
            "active": 0.2,  # 活跃时少回复
            "hot": 0.05,    # 火热时极少回复
        }

        should_reply = random.random() < probabilities[activity]
        logger.debug(f"活跃度: {activity}, 回复: {should_reply}")
        return should_reply

    async def _get_activity_level(self, conv_id: str) -> str:
        """获取群聊活跃度"""
        key = f"ai_chat:activity:{conv_id}"

        # 记录消息
        await redis_client.lpush(key, datetime.now().isoformat())
        await redis_client.ltrim(key, 0, 100)
        await redis_client.expire(key, self.config.activity_window)

        # 统计最近消息数
        messages = await redis_client.lrange(key, 0, -1)
        now = datetime.now()
        recent_count = 0

        for msg_time_str in messages:
            try:
                msg_time = datetime.fromisoformat(msg_time_str)
                if (now - msg_time).total_seconds() <= self.config.activity_window:
                    recent_count += 1
            except Exception:
                continue

        # 判断活跃度（使用配置的阈值）
        if recent_count <= self.config.activity_cold_threshold:
            return "cold"
        elif recent_count <= self.config.activity_normal_threshold:
            return "normal"
        elif recent_count <= self.config.activity_active_threshold:
            return "active"
        else:
            return "hot"

    # ==================== 策略 4: 对话轮次限制 ====================

    async def _strategy_turns(self, conv_id: str, is_at: bool) -> bool:
        """对话轮次限制策略"""
        # @机器人总是回复
        if is_at:
            return True

        if not self.config.enable_turn_limit:
            return True

        key = f"ai_chat:turns:{conv_id}"
        turns = await redis_client.get(key)
        current_turns = int(turns) if turns else 0

        if current_turns >= self.config.max_conversation_turns:
            # 超过限制，重置计数
            await redis_client.delete(key)
            logger.debug(f"对话轮次超限 ({current_turns}), 跳过回复")
            return False

        # 增加轮次
        await redis_client.incr(key)
        await redis_client.expire(key, self.config.turn_reset_seconds)

        logger.debug(f"对话轮次: {current_turns + 1}/{self.config.max_conversation_turns}")
        return True

    # ==================== 策略 5: 概率控制（备用） ====================

    async def _strategy_probability(self, conv_id: str) -> bool:
        """概率控制策略"""
        if not self.config.enable_probability_control:
            return True

        # 获取最近回复次数
        key = f"ai_chat:reply_count:{conv_id}"
        count = await redis_client.get(key)
        recent_count = int(count) if count else 0

        # 根据最近回复次数调整概率
        adjusted_prob = self.config.base_reply_probability * (0.8 ** recent_count)

        if random.random() < adjusted_prob:
            # 增加计数
            await redis_client.incr(key)
            await redis_client.expire(key, 3600)
            return True

        return False
