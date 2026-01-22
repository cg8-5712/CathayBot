# CathayBot - 高度插件化 NoneBot2 QQ 机器人

## 项目概述

基于 NoneBot2 的高度插件化 QQ 机器人框架，采用模块化设计，支持插件独立配置、统计分析、WebUI 管理等功能。

## 技术栈

- **框架**: NoneBot2 + OneBot V11
- **驱动**: FastAPI
- **配置**: YAML + Pydantic2
- **数据库**: SQLite/PostgreSQL (待定)
- **前端**: Vue3 (WebUI)

---

## 目录结构

```
CathayBot/
├── bot.py                    # 入口文件
├── pyproject.toml            # 项目依赖
├── configs/                  # 配置目录
│   ├── config.yaml           # 全局配置
│   └── plugins/              # 插件配置目录
│       ├── help.yaml
│       ├── statistics.yaml
│       └── ...
├── cathaybot/                # 核心模块
│   ├── __init__.py
│   ├── config.py             # 全局配置加载 (Pydantic2)
│   ├── database/             # 数据库抽象层
│   │   ├── __init__.py
│   │   ├── models.py         # 数据模型
│   │   └── crud.py           # CRUD 操作
│   └── utils/                # 工具函数
│       ├── __init__.py
│       └── plugin_meta.py    # 插件元信息读取
├── plugins/                  # 插件目录
│   ├── help/                 # 自动帮助生成插件
│   ├── statistics/           # 统计插件 (发言/调用)
│   ├── admin/                # 管理员命令插件
│   ├── webui/                # WebUI 插件 (独立可复用)
│   └── web_qq/               # Web版QQ插件 (大项目)
├── data/                     # 数据存储
│   ├── db.sqlite             # 数据库文件
│   └── cache/                # 缓存目录
└── logs/                     # 日志目录
```

---

## 配置系统设计

### 全局配置 (`configs/config.yaml`)

```yaml
bot:
  superusers: ["123456789"]    # 超级管理员QQ
  nickname: ["CathayBot"]
  command_start: ["/", "!"]
  command_sep: ["."]

database:
  type: sqlite                 # sqlite / postgresql
  path: ./data/db.sqlite       # SQLite 路径
  # url: postgresql://...      # PostgreSQL 连接串

webui:
  enabled: true
  host: 0.0.0.0
  port: 8081
  secret_key: "your-secret-key"
```

### 插件配置模板

每个插件在 `configs/plugins/` 下有独立配置文件，通过 Pydantic2 模型验证：

```python
# 插件配置基类
from pydantic import BaseModel
from pathlib import Path
import yaml

class PluginConfig(BaseModel):
    enabled: bool = True

    @classmethod
    def load(cls, plugin_name: str) -> "PluginConfig":
        config_path = Path(f"configs/plugins/{plugin_name}.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return cls(**yaml.safe_load(f))
        return cls()
```

---

## 核心插件规划

### 1. Help 插件 (`plugins/help/`)

**功能**: 自动扫描所有插件，生成帮助信息

**实现思路**:
- 读取每个插件的 `__init__.py` 中的 `__plugin_meta__`
- 支持 NoneBot2 标准的 `PluginMetadata`
- 按分类整理，支持分页显示

**命令**:
- `/help` - 显示所有插件列表
- `/help <插件名>` - 显示插件详细帮助

### 2. Statistics 插件 (`plugins/statistics/`)

**功能**: 统计群发言次数、插件调用次数

**数据模型**:
```python
class MessageRecord(Base):
    id: int
    user_id: str
    group_id: str
    message_type: str
    timestamp: datetime

class PluginCallRecord(Base):
    id: int
    plugin_name: str
    user_id: str
    group_id: str
    command: str
    timestamp: datetime
```

**命令**:
- `/stat today` - 今日群统计
- `/stat week` - 本周统计
- `/stat user @xxx` - 用户统计
- `/stat plugin` - 插件调用排行

### 3. Admin 插件 (`plugins/admin/`)

**功能**: 管理员专用命令

**命令**:
- `/admin reload <插件名>` - 重载插件
- `/admin enable/disable <插件名>` - 启用/禁用插件
- `/admin broadcast <消息>` - 群发消息
- `/admin ban <QQ>` - 封禁用户
- `/admin status` - 机器人状态

### 4. WebUI 插件 (`plugins/webui/`)

**设计原则**: 完全独立，可单独发布到 PyPI

**功能**:
- 仪表盘：在线状态、消息统计图表
- 插件管理：启用/禁用/配置
- 日志查看
- 配置编辑器

**技术方案**:
- 后端：FastAPI 路由挂载到 NoneBot driver
- 前端：Vue3 SPA，打包后嵌入插件
- 认证：JWT Token

**目录结构**:
```
plugins/webui/
├── __init__.py           # 插件入口
├── config.py             # WebUI 配置
├── api/                  # API 路由
│   ├── __init__.py
│   ├── auth.py           # 认证接口
│   ├── dashboard.py      # 仪表盘数据
│   ├── plugins.py        # 插件管理
│   └── logs.py           # 日志接口
├── static/               # 前端静态文件
│   └── dist/             # Vue 打包产物
└── frontend/             # 前端源码 (开发用)
    ├── package.json
    └── src/
```

### 5. Web QQ 插件 (`plugins/web_qq/`) - 大项目

**功能**: 基于聊天记录的 Web 版 QQ 体验

**核心模块**:

#### 5.1 消息存储
- 实时存储所有收到的消息
- 支持文本、图片、表情、文件等类型
- 消息索引与全文搜索

#### 5.2 图片/表情包管理
```python
class ImageRecord(Base):
    id: int
    file_id: str              # QQ 文件ID
    local_path: str           # 本地存储路径
    url: str                  # 原始URL
    message_id: int           # 关联消息
    is_emoji: bool            # 是否为表情包
    tags: list[str]           # 标签 (用于搜索)
    created_at: datetime
```

#### 5.3 聊天记录管理
- 按群/私聊分类
- 时间线浏览
- 关键词搜索
- 消息导出 (JSON/HTML)

#### 5.4 Web 界面
- 仿 QQ 界面设计
- 左侧：会话列表
- 右侧：聊天记录
- 支持图片预览、表情包收藏

**数据模型**:
```python
class Conversation(Base):
    """会话 (群/私聊)"""
    id: int
    conv_type: str            # group / private
    target_id: str            # 群号或QQ号
    name: str                 # 群名或昵称
    avatar: str               # 头像
    last_message_at: datetime
    unread_count: int

class Message(Base):
    """消息记录"""
    id: int
    conversation_id: int
    sender_id: str
    sender_name: str
    content: str              # 消息内容 (JSON格式)
    message_type: str         # text/image/face/file/...
    raw_message: str          # 原始消息
    timestamp: datetime

class EmojiCollection(Base):
    """表情包收藏"""
    id: int
    user_id: str
    image_id: int
    category: str             # 分类
    created_at: datetime
```

---

## 开发计划

### Phase 1: 基础架构
- [ ] 创建项目目录结构
- [ ] 实现配置系统 (YAML + Pydantic2)
- [ ] 搭建数据库抽象层
- [ ] 创建插件配置基类

### Phase 2: 核心插件
- [ ] Help 插件 - 自动帮助生成
- [ ] Statistics 插件 - 发言/调用统计
- [ ] Admin 插件 - 管理员命令

### Phase 3: WebUI 插件
- [ ] 后端 API 框架
- [ ] 认证系统
- [ ] 前端界面开发
- [ ] 打包与发布

### Phase 4: Web QQ 插件
- [ ] 消息存储系统
- [ ] 图片/表情包管理
- [ ] 聊天记录 API
- [ ] Web 界面开发
- [ ] 搜索功能

---

## 插件开发规范

### 插件元信息

每个插件必须在 `__init__.py` 中定义 `__plugin_meta__`:

```python
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="插件名称",
    description="插件描述",
    usage="""
    /command1 - 功能1
    /command2 - 功能2
    """,
    type="application",
    homepage="https://github.com/...",
    config=PluginConfig,  # 插件配置类
    extra={
        "author": "作者",
        "version": "1.0.0",
        "category": "工具",  # 用于 help 分类
    }
)
```

### 插件配置

```python
from pydantic import BaseModel

class Config(BaseModel):
    """插件配置"""
    enabled: bool = True
    some_option: str = "default"
```

---

## 注意事项

1. **WebUI 独立性**: WebUI 插件设计为完全独立，不依赖 CathayBot 特有功能，可发布到 PyPI 供其他 NoneBot 项目使用

2. **数据安全**: Web QQ 涉及聊天记录存储，需要：
   - 访问权限控制
   - 数据加密存储 (可选)
   - 定期清理策略

3. **性能考虑**:
   - 消息存储使用异步写入
   - 图片采用懒加载
   - 大量数据分页处理

4. **兼容性**:
   - 支持 OneBot V11 协议
   - 预留 OneBot V12 适配接口
