"""
AI Chat 插件配置
"""

from cathaybot.utils.plugin_config import PluginConfig
from pydantic import Field


class Config(PluginConfig):
    """AI Chat 插件配置"""

    # AI 提供商: openai / claude / local
    provider: str = Field(default="openai", description="AI 提供商")

    # API 配置
    api_key: str = Field(default="", description="API Key")
    api_base: str = Field(default="", description="API Base URL (可选)")
    model: str = Field(default="gpt-4o-mini", description="模型名称")

    # 触发配置
    trigger_on_at: bool = Field(default=True, description="@机器人时触发")
    trigger_on_reply: bool = Field(default=True, description="回复机器人消息时触发")
    trigger_keywords: list[str] = Field(default_factory=list, description="触发关键词列表")
    random_reply_probability: float = Field(default=0.0, description="随机回复概率 (0.0-1.0)")

    # 上下文配置
    max_context_messages: int = Field(default=20, description="最大上下文消息数")
    context_expire_seconds: int = Field(default=3600, description="上下文过期时间（秒）")
    enable_context: bool = Field(default=True, description="是否启用上下文")

    # Prompt 配置
    system_prompt: str = Field(
        default="""你是一个友好、幽默的 AI 助手，正在群聊中与大家交流。
你的回复应该：
1. 简洁自然，符合聊天语境
2. 适当使用表情和网络用语
3. 不要过于正式或啰嗦
4. 可以开玩笑，但要注意分寸
5. 如果不确定，可以坦诚说不知道

当前群聊：{group_name}
当前用户：{user_name}""",
        description="系统提示词",
    )

    # 分群 Prompt (可选，覆盖全局 prompt)
    group_prompts: dict[str, str] = Field(default_factory=dict, description="分群自定义 Prompt")

    # 回复配置
    max_reply_length: int = Field(default=500, description="最大回复长度")
    reply_timeout: int = Field(default=30, description="回复超时时间（秒）")

    # 分段发送配置（模拟真人聊天）
    split_message: bool = Field(default=True, description="是否分段发送消息")
    split_max_length: int = Field(default=80, description="每段消息最大长度")
    split_delay_min: float = Field(default=0.3, description="分段发送最小间隔（秒）")
    split_delay_max: float = Field(default=1.2, description="分段发送最大间隔（秒）")

    # 过滤配置
    enable_content_filter: bool = Field(default=True, description="是否启用内容过滤")
    blocked_words: list[str] = Field(default_factory=list, description="敏感词列表")

    # 功能开关
    enable_image_recognition: bool = Field(default=False, description="是否启用图片识别")
    enable_memory: bool = Field(default=True, description="是否启用记忆功能")

    # 速率限制
    rate_limit_per_user: int = Field(default=10, description="每用户每分钟最大请求数")
    rate_limit_per_group: int = Field(default=30, description="每群每分钟最大请求数")

    # 负载优化配置
    enable_cooldown: bool = Field(default=True, description="是否启用冷却时间")
    cooldown_seconds: int = Field(default=30, description="群聊冷却时间（秒）")
    cooldown_per_user: int = Field(default=10, description="单用户冷却时间（秒）")

    enable_smart_skip: bool = Field(default=True, description="是否智能跳过简单消息")
    min_message_length: int = Field(default=3, description="最小消息长度")

    # 智能回复策略
    reply_strategy: str = Field(
        default="chat",
        description="回复策略: chat(闲聊) / importance(重要性) / priority(优先级) / activity(活跃度) / turns(轮次) / probability(概率)"
    )

    # ========== Chat 闲聊模式配置 ==========

    # 活跃度判断阈值
    activity_cold_threshold: int = Field(default=5, description="冷清阈值（消息数/分钟）")
    activity_normal_threshold: int = Field(default=15, description="正常阈值（消息数/分钟）")
    activity_active_threshold: int = Field(default=30, description="活跃阈值（消息数/分钟）")

    # 各活跃度下的基础回复概率
    chat_prob_cold: float = Field(default=0.6, description="冷清时回复概率")
    chat_prob_normal: float = Field(default=0.3, description="正常时回复概率")
    chat_prob_active: float = Field(default=0.5, description="活跃时回复概率")
    chat_prob_hot: float = Field(default=0.6, description="火热时回复概率")

    # 有趣话题词（触发更高回复概率）
    interesting_topics: list[str] = Field(
        default_factory=lambda: [
            "游戏", "电影", "音乐", "美食", "旅游", "八卦", "搞笑",
            "有意思", "好玩", "厉害", "牛", "哈哈", "笑死", "绝了",
            "今天", "刚才", "听说", "你们", "大家"
        ],
        description="有趣话题词列表"
    )

    # 冷却中的概率衰减系数
    cooldown_decay: float = Field(default=0.3, description="冷却中概率衰减系数")

    # 重要性策略配置
    importance_threshold: float = Field(default=0.3, description="重要性阈值 (0.0-1.0)")

    # 轮次限制配置
    enable_turn_limit: bool = Field(default=True, description="是否启用对话轮次限制")
    max_conversation_turns: int = Field(default=3, description="最大连续对话轮次")
    turn_reset_seconds: int = Field(default=300, description="轮次重置时间（秒）")

    # 活跃度自适应配置
    enable_activity_adaptive: bool = Field(default=False, description="是否启用活跃度自适应")
    activity_window: int = Field(default=60, description="活跃度统计窗口（秒）")

    # 概率控制配置（备用）
    enable_probability_control: bool = Field(default=False, description="是否启用概率控制")
    base_reply_probability: float = Field(default=0.7, description="基础回复概率 (0.0-1.0)")

    enable_context_compression: bool = Field(default=True, description="是否启用上下文压缩")
    keep_recent_messages: int = Field(default=5, description="保留最近N条完整消息")
