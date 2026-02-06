# AI Chat 配置指南

## 📍 配置文件位置

```
configs/plugins/ai_chat.yaml
```

---

## 🎯 快速开始

### 1. 基础配置（必填）

```yaml
# AI 提供商
provider: openai  # 或 claude
api_key: "your-api-key-here"  # 必填
model: "gpt-4o-mini"

# 触发方式
trigger_on_at: true  # @机器人触发
trigger_on_reply: true  # 回复机器人消息触发
```

### 2. 选择回复策略

```yaml
# 闲聊型机器人（推荐）
reply_strategy: chat

# 问答型机器人
reply_strategy: importance
```

---

## 🎭 Chat 闲聊模式配置（详细）

### 活跃度阈值

控制如何判断群聊活跃度：

```yaml
activity_cold_threshold: 5    # ≤5条/分钟 = 冷清
activity_normal_threshold: 15  # ≤15条/分钟 = 正常
activity_active_threshold: 30  # ≤30条/分钟 = 活跃
# >30条/分钟 = 火热
```

**调优建议：**
- 小群（<50人）：保持默认
- 大群（>100人）：提高阈值（10/25/50）
- 水群：降低阈值（3/10/20）

---

### 回复概率

控制不同活跃度下的回复频率：

```yaml
chat_prob_cold: 0.6    # 冷清时：60% 概率
chat_prob_normal: 0.3  # 正常时：30% 概率
chat_prob_active: 0.5  # 活跃时：50% 概率
chat_prob_hot: 0.6     # 火热时：60% 概率
```

**调优建议：**

| 需求 | cold | normal | active | hot |
|------|------|--------|--------|-----|
| **更活跃** | 0.8 | 0.5 | 0.7 | 0.8 |
| **默认** | 0.6 | 0.3 | 0.5 | 0.6 |
| **更安静** | 0.4 | 0.2 | 0.3 | 0.4 |

---

### 有趣话题词

包含这些词的消息更容易触发回复：

```yaml
interesting_topics:
  - "游戏"
  - "电影"
  - "音乐"
  # ... 添加你的群聊常见话题
```

**自定义建议：**
- 技术群：添加 "代码"、"框架"、"算法"
- 游戏群：添加 "开黑"、"上分"、"皮肤"
- 二次元群：添加 "番剧"、"cos"、"手办"

---

### 冷却衰减

冷却期间的概率衰减：

```yaml
cooldown_decay: 0.3  # 冷却中概率降低到 30%
```

**说明：**
- `0.0`：冷却期间完全不回复
- `0.3`：冷却期间概率降低到 30%（推荐）
- `1.0`：冷却期间不受影响

---

## 🔧 其他重要配置

### 冷却时间

```yaml
enable_cooldown: true
cooldown_seconds: 30      # 群聊冷却（秒）
cooldown_per_user: 10     # 用户冷却（秒）
```

**调优：**
- 更活跃：`cooldown_seconds: 20`
- 更安静：`cooldown_seconds: 60`

---

### 对话轮次限制

```yaml
enable_turn_limit: true
max_conversation_turns: 3  # 连续对话3轮后退出
turn_reset_seconds: 300    # 5分钟后重置
```

**说明：** 避免 AI 霸占话题

---

### 分段发送

```yaml
split_message: true
split_max_length: 80       # 每段最大长度
split_delay_min: 0.3       # 最小间隔（秒）
split_delay_max: 1.2       # 最大间隔（秒）
```

**效果：** 模拟真人打字，分段发送

---

### 上下文管理

```yaml
max_context_messages: 20   # 最大上下文消息数
context_expire_seconds: 3600  # 1小时过期
enable_context_compression: true
keep_recent_messages: 5    # 保留最近5条完整消息
```

---

## 📊 配置示例

### 示例 1：活跃的闲聊群友

```yaml
reply_strategy: chat

# 活跃度阈值
activity_cold_threshold: 5
activity_normal_threshold: 15
activity_active_threshold: 30

# 回复概率（更活跃）
chat_prob_cold: 0.8
chat_prob_normal: 0.5
chat_prob_active: 0.7
chat_prob_hot: 0.8

# 冷却时间（更短）
cooldown_seconds: 20
cooldown_per_user: 8

# 对话轮次（更多）
max_conversation_turns: 5
```

**效果：** 非常活跃，积极参与聊天

---

### 示例 2：安静的潜水群友

```yaml
reply_strategy: chat

# 回复概率（更安静）
chat_prob_cold: 0.4
chat_prob_normal: 0.2
chat_prob_active: 0.3
chat_prob_hot: 0.4

# 冷却时间（更长）
cooldown_seconds: 60
cooldown_per_user: 20

# 对话轮次（更少）
max_conversation_turns: 2
```

**效果：** 比较安静，偶尔冒泡

---

### 示例 3：问答型助手

```yaml
reply_strategy: importance
importance_threshold: 0.3

# 冷却时间
cooldown_seconds: 30

# 对话轮次
max_conversation_turns: 3
```

**效果：** 只回答问题，不参与闲聊

---

## 🎨 自定义 Prompt

### 全局 Prompt

```yaml
system_prompt: |
  你是一个友好、幽默的 AI 助手。
  你的性格：
  - 活泼开朗，喜欢开玩笑
  - 会用网络用语和表情
  - 不会过于正式

  当前群聊：{group_name}
  当前用户：{user_name}
```

### 分群 Prompt

```yaml
group_prompts:
  "123456789": |
    你是技术群的助手，擅长编程问题。
  "987654321": |
    你是游戏群的群友，喜欢讨论游戏。
```

---

## 🔍 调试技巧

### 查看日志

日志会显示详细的决策过程：

```
闲聊模式 - 活跃度: active, 有趣度: 0.75, 概率: 0.60, 回复: True
```

### 测试配置

1. 修改配置文件
2. 重启机器人
3. 在群里发消息测试
4. 查看日志调整参数

---

## ❓ 常见问题

### Q: 回复太频繁怎么办？

A: 降低回复概率或增加冷却时间：
```yaml
chat_prob_normal: 0.2  # 降低
cooldown_seconds: 60   # 增加
```

### Q: 回复太少怎么办？

A: 提高回复概率或降低冷却时间：
```yaml
chat_prob_cold: 0.8    # 提高
cooldown_seconds: 15   # 降低
```

### Q: 只想回答问题，不想闲聊？

A: 切换到 importance 模式：
```yaml
reply_strategy: importance
```

### Q: 如何添加自定义话题词？

A: 编辑 `interesting_topics` 列表：
```yaml
interesting_topics:
  - "你的话题1"
  - "你的话题2"
```

---

## 📝 配置文件完整示例

```yaml
# 基础配置
provider: openai
api_key: "sk-..."
model: "gpt-4o-mini"

# 触发配置
trigger_on_at: true
trigger_on_reply: true
trigger_keywords: []

# 上下文配置
max_context_messages: 20
context_expire_seconds: 3600
enable_context: true

# Prompt
system_prompt: |
  你是一个友好的 AI 助手...

# 回复配置
max_reply_length: 500
split_message: true
split_max_length: 80
split_delay_min: 0.3
split_delay_max: 1.2

# 冷却配置
enable_cooldown: true
cooldown_seconds: 30
cooldown_per_user: 10

# 智能跳过
enable_smart_skip: true
min_message_length: 3

# 回复策略
reply_strategy: chat

# Chat 模式配置
activity_cold_threshold: 5
activity_normal_threshold: 15
activity_active_threshold: 30

chat_prob_cold: 0.6
chat_prob_normal: 0.3
chat_prob_active: 0.5
chat_prob_hot: 0.6

interesting_topics:
  - "游戏"
  - "电影"
  # ...

cooldown_decay: 0.3

# 轮次限制
enable_turn_limit: true
max_conversation_turns: 3
turn_reset_seconds: 300

# 上下文压缩
enable_context_compression: true
keep_recent_messages: 5
```

---

## 🚀 快速调优流程

1. **确定定位**：闲聊型 or 问答型？
2. **选择策略**：`chat` or `importance`
3. **调整概率**：太多就降低，太少就提高
4. **调整冷却**：太频繁就增加，太少就降低
5. **自定义话题**：添加群聊常见话题词
6. **测试调整**：实际使用中微调

---

配置文件位置：`configs/plugins/ai_chat.yaml`

修改后重启机器人即可生效！
