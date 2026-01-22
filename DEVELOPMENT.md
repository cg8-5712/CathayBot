# CathayBot 开发指南

本文档详细说明项目的架构设计、开发规范和实现计划。

---

## 目录

1. [基础架构](#基础架构)
2. [配置系统](#配置系统)
3. [数据库设计](#数据库设计)
4. [插件开发规范](#插件开发规范)
5. [核心插件实现](#核心插件实现)
6. [开发计划](#开发计划)

---

## 基础架构

### 目录结构详解

```
CathayBot/
├── bot.py                        # 入口文件
├── pyproject.toml                # 项目依赖 (Poetry)
├── requirements.txt              # 依赖列表 (pip)
│
├── configs/                      # 配置目录
│   ├── config.yaml               # 全局配置
│   ├── config.example.yaml       # 配置模板
│   └── plugins/                  # 插件配置目录
│       ├── help.yaml
│       ├── statistics.yaml
│       ├── admin.yaml
│       ├── webui.yaml
│       └── web_qq.yaml
│
├── cathaybot/                    # 核心模块
│   ├── __init__.py               # 模块初始化
│   ├── config.py                 # 全局配置加载器
│   ├── database/                 # 数据库抽象层
│   │   ├── __init__.py
│   │   ├── connection.py         # 数据库连接管理
│   │   ├── models.py             # SQLAlchemy 模型基类
│   │   └── crud.py               # 通用 CRUD 操作
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── plugin_config.py      # 插件配置基类
│       └── plugin_meta.py        # 插件元信息工具
│
├── plugins/                      # 插件目录
│   ├── help/                     # 帮助插件
│   │   ├── __init__.py
│   │   └── config.py
│   ├── statistics/               # 统计插件
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── models.py
│   ├── admin/                    # 管理插件
│   │   ├── __init__.py
│   │   └── config.py
│   ├── webui/                    # WebUI 插件 (独立)
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── api/
│   │   ├── static/
│   │   └── frontend/
│   └── web_qq/                   # Web QQ 插件
│       ├── __init__.py
│       ├── config.py
│       ├── models.py
│       ├── api/
│       └── frontend/
│
├── data/                         # 数据存储
│   ├── db.sqlite                 # SQLite 数据库
│   ├── images/                   # 图片存储
│   └── cache/                    # 缓存目录
│
└── logs/                         # 日志目录
    └── cathaybot.log
```

### 核心模块说明

#### `cathaybot/config.py` - 全局配置加载器

负责加载和验证 `configs/config.yaml`：

```python
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import yaml

class BotConfig(BaseModel):
    superusers: list[str] = []
    nickname: list[str] = ["CathayBot"]
    command_start: list[str] = ["/", "!"]
    command_sep: list[str] = ["."]

class DatabaseConfig(BaseModel):
    type: str = "sqlite"
    path: str = "./data/db.sqlite"
    url: Optional[str] = None

class WebUIConfig(BaseModel):
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8081
    secret_key: str = "change-me-in-production"

class GlobalConfig(BaseModel):
    bot: BotConfig = BotConfig()
    database: DatabaseConfig = DatabaseConfig()
    webui: WebUIConfig = WebUIConfig()

    @classmethod
    def load(cls, config_path: str = "configs/config.yaml") -> "GlobalConfig":
        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return cls(**data)
        return cls()

# 全局配置实例
config = GlobalConfig.load()
```

#### `cathaybot/utils/plugin_config.py` - 插件配置基类

```python
from pathlib import Path
from typing import TypeVar, Type
from pydantic import BaseModel
import yaml

T = TypeVar("T", bound="PluginConfig")

class PluginConfig(BaseModel):
    """插件配置基类"""
    enabled: bool = True

    @classmethod
    def load(cls: Type[T], plugin_name: str) -> T:
        """从 YAML 文件加载插件配置"""
        config_path = Path(f"configs/plugins/{plugin_name}.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return cls(**data)
        return cls()

    def save(self, plugin_name: str) -> None:
        """保存配置到 YAML 文件"""
        config_path = Path(f"configs/plugins/{plugin_name}.yaml")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, default_flow_style=False)
```

---

## 配置系统

### 全局配置文件

`configs/config.yaml`:

```yaml
# CathayBot 全局配置

bot:
  superusers:
    - "123456789"           # 超级管理员 QQ 号
  nickname:
    - "CathayBot"
    - "小猫"
  command_start:
    - "/"
    - "!"
  command_sep:
    - "."

database:
  type: sqlite              # sqlite / postgresql
  path: ./data/db.sqlite    # SQLite 文件路径
  # url: postgresql://user:pass@localhost:5432/cathaybot  # PostgreSQL

webui:
  enabled: true
  host: 0.0.0.0
  port: 8081
  secret_key: "your-secret-key-change-in-production"

logging:
  level: INFO               # DEBUG / INFO / WARNING / ERROR
  file: ./logs/cathaybot.log
  max_size: 10485760        # 10MB
  backup_count: 5
```

### 插件配置示例

`configs/plugins/statistics.yaml`:

```yaml
enabled: true

# 统计配置
track_messages: true        # 是否统计消息
track_commands: true        # 是否统计命令调用
ignore_bots: true           # 是否忽略机器人消息

# 数据保留
retention_days: 90          # 数据保留天数 (0=永久)

# 排行榜
top_limit: 10               # 排行榜显示数量
```

`configs/plugins/webui.yaml`:

```yaml
enabled: true

host: 0.0.0.0
port: 8081

# 认证配置
auth:
  secret_key: "your-jwt-secret"
  token_expire_hours: 24

# 管理员账号
admin:
  username: admin
  password_hash: ""         # bcrypt hash，首次运行时设置
```

---

## 数据库设计

### 连接管理

`cathaybot/database/connection.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from cathaybot.config import config

class Base(DeclarativeBase):
    pass

# 根据配置创建引擎
if config.database.type == "sqlite":
    DATABASE_URL = f"sqlite+aiosqlite:///{config.database.path}"
else:
    DATABASE_URL = config.database.url

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """获取数据库会话"""
    async with async_session() as session:
        yield session
```

### 通用模型

`cathaybot/database/models.py`:

```python
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from .connection import Base

class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 插件开发规范

### 插件结构

每个插件是 `plugins/` 下的一个目录：

```
plugins/my_plugin/
├── __init__.py           # 插件入口，必须包含 __plugin_meta__
├── config.py             # 插件配置类 (可选)
├── models.py             # 数据模型 (可选)
├── handlers.py           # 事件处理器 (可选，大型插件拆分用)
└── utils.py              # 工具函数 (可选)
```

### 插件元信息

每个插件必须在 `__init__.py` 中定义 `__plugin_meta__`：

```python
from nonebot import on_command
from nonebot.plugin import PluginMetadata
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="插件名称",
    description="插件的简短描述",
    usage="""
/command1 - 功能说明1
/command2 <参数> - 功能说明2
    """.strip(),
    type="application",
    homepage="https://github.com/...",
    config=Config,
    extra={
        "author": "作者名",
        "version": "1.0.0",
        "category": "工具",      # 用于 help 分类: 工具/管理/娱乐/其他
        "priority": 10,          # 显示优先级 (可选)
    }
)
```

### 插件配置类

```python
# plugins/my_plugin/config.py
from cathaybot.utils.plugin_config import PluginConfig

class Config(PluginConfig):
    """我的插件配置"""
    enabled: bool = True
    some_option: str = "default"
    max_count: int = 100

# 加载配置
plugin_config = Config.load("my_plugin")
```

### 事件处理器示例

```python
# plugins/my_plugin/__init__.py
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from .config import Config

__plugin_meta__ = PluginMetadata(...)

# 加载配置
config = Config.load("my_plugin")

# 命令处理器
my_cmd = on_command("mycmd", priority=10, block=True)

@my_cmd.handle()
async def handle_mycmd(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()
    await my_cmd.finish(f"收到参数: {arg_text}")

# 消息处理器 (监听所有消息)
msg_handler = on_message(priority=99, block=False)

@msg_handler.handle()
async def handle_msg(event: GroupMessageEvent):
    # 处理群消息
    pass
```

---

## 核心插件实现

### 1. Help 插件

**功能**: 自动扫描所有插件，生成帮助信息

**实现要点**:

```python
# plugins/help/__init__.py
from nonebot import get_loaded_plugins, on_command
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="帮助",
    description="显示所有插件的帮助信息",
    usage="/help - 显示插件列表\n/help <插件名> - 显示插件详情",
    extra={"author": "CathayBot", "version": "1.0.0", "category": "工具"}
)

help_cmd = on_command("help", priority=1, block=True)

@help_cmd.handle()
async def handle_help(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()

    if not arg:
        # 显示所有插件列表
        plugins = get_loaded_plugins()
        msg = "📚 插件列表:\n\n"

        # 按 category 分组
        categories = {}
        for plugin in plugins:
            if plugin.metadata:
                cat = plugin.metadata.extra.get("category", "其他")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(plugin.metadata.name)

        for cat, names in categories.items():
            msg += f"【{cat}】\n"
            msg += "、".join(names) + "\n\n"

        msg += "使用 /help <插件名> 查看详情"
        await help_cmd.finish(msg)
    else:
        # 显示指定插件详情
        for plugin in get_loaded_plugins():
            if plugin.metadata and plugin.metadata.name == arg:
                meta = plugin.metadata
                msg = f"📖 {meta.name}\n\n"
                msg += f"描述: {meta.description}\n\n"
                msg += f"用法:\n{meta.usage}\n\n"
                msg += f"版本: {meta.extra.get('version', '未知')}\n"
                msg += f"作者: {meta.extra.get('author', '未知')}"
                await help_cmd.finish(msg)

        await help_cmd.finish(f"未找到插件: {arg}")
```

### 2. Statistics 插件

**功能**: 统计群发言次数、插件调用次数

**数据模型**:

```python
# plugins/statistics/models.py
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from cathaybot.database.connection import Base

class MessageRecord(Base):
    """消息记录"""
    __tablename__ = "message_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), index=True)
    group_id: Mapped[str] = mapped_column(String(20), index=True, nullable=True)
    message_type: Mapped[str] = mapped_column(String(20))  # group / private
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class CommandRecord(Base):
    """命令调用记录"""
    __tablename__ = "command_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plugin_name: Mapped[str] = mapped_column(String(50), index=True)
    command: Mapped[str] = mapped_column(String(50), index=True)
    user_id: Mapped[str] = mapped_column(String(20), index=True)
    group_id: Mapped[str] = mapped_column(String(20), index=True, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
```

### 3. Admin 插件

**功能**: 管理员专用命令

**权限检查**:

```python
# plugins/admin/__init__.py
from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="管理",
    description="管理员命令",
    usage="""
/admin status - 机器人状态
/admin reload <插件> - 重载插件
/admin enable <插件> - 启用插件
/admin disable <插件> - 禁用插件
    """.strip(),
    extra={"author": "CathayBot", "version": "1.0.0", "category": "管理"}
)

admin_cmd = on_command("admin", permission=SUPERUSER, priority=1, block=True)
```

### 4. WebUI 插件

**设计原则**: 完全独立，可发布到 PyPI

**目录结构**:

```
plugins/webui/
├── __init__.py           # 插件入口，注册路由
├── config.py             # WebUI 配置
├── api/                  # API 路由
│   ├── __init__.py       # 路由注册
│   ├── auth.py           # 认证: POST /api/login, /api/logout
│   ├── dashboard.py      # 仪表盘: GET /api/dashboard
│   ├── plugins.py        # 插件管理: GET/POST /api/plugins
│   └── logs.py           # 日志: GET /api/logs
├── static/               # 前端静态文件
│   └── dist/             # Vue 打包产物
└── frontend/             # 前端源码 (开发用)
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── App.vue
        ├── views/
        └── components/
```

**路由注册**:

```python
# plugins/webui/__init__.py
from nonebot import get_driver
from nonebot.plugin import PluginMetadata
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

__plugin_meta__ = PluginMetadata(
    name="WebUI",
    description="Web 管理面板",
    usage="访问 http://localhost:8081",
    extra={"author": "CathayBot", "version": "1.0.0", "category": "管理"}
)

driver = get_driver()

@driver.on_startup
async def register_routes():
    app: FastAPI = driver.server_app

    # 注册 API 路由
    from .api import router
    app.include_router(router, prefix="/api")

    # 挂载静态文件
    static_path = Path(__file__).parent / "static" / "dist"
    if static_path.exists():
        app.mount("/", StaticFiles(directory=static_path, html=True), name="webui")
```

### 5. Web QQ 插件

**核心模块**:

```
plugins/web_qq/
├── __init__.py           # 插件入口
├── config.py             # 配置
├── models.py             # 数据模型
├── storage/              # 存储模块
│   ├── __init__.py
│   ├── message.py        # 消息存储
│   └── image.py          # 图片存储
├── api/                  # API 路由
│   ├── __init__.py
│   ├── conversations.py  # 会话列表
│   ├── messages.py       # 消息记录
│   ├── images.py         # 图片管理
│   └── search.py         # 搜索功能
└── frontend/             # 前端 (仿 QQ 界面)
```

**数据模型**:

```python
# plugins/web_qq/models.py
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from cathaybot.database.connection import Base

class Conversation(Base):
    """会话"""
    __tablename__ = "webqq_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conv_type: Mapped[str] = mapped_column(String(10))  # group / private
    target_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar: Mapped[str] = mapped_column(String(500), nullable=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_message_preview: Mapped[str] = mapped_column(String(100), nullable=True)

class Message(Base):
    """消息"""
    __tablename__ = "webqq_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(Integer, index=True)
    message_id: Mapped[str] = mapped_column(String(50), unique=True)
    sender_id: Mapped[str] = mapped_column(String(20), index=True)
    sender_name: Mapped[str] = mapped_column(String(50))
    sender_avatar: Mapped[str] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(JSON)  # 结构化消息内容
    raw_message: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)

class Image(Base):
    """图片"""
    __tablename__ = "webqq_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[str] = mapped_column(String(100), unique=True)
    local_path: Mapped[str] = mapped_column(String(500))
    original_url: Mapped[str] = mapped_column(String(500))
    message_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    is_emoji: Mapped[bool] = mapped_column(Boolean, default=False)
    width: Mapped[int] = mapped_column(Integer, nullable=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class EmojiCollection(Base):
    """表情包收藏"""
    __tablename__ = "webqq_emoji_collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), index=True)
    image_id: Mapped[int] = mapped_column(Integer, index=True)
    category: Mapped[str] = mapped_column(String(50), default="默认")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

## 开发计划

### Phase 1: 基础架构 ✅ 规划完成

- [ ] 创建目录结构
  - [ ] `cathaybot/` 核心模块目录
  - [ ] `configs/` 配置目录
  - [ ] `data/` 数据目录
  - [ ] `logs/` 日志目录

- [ ] 实现配置系统
  - [ ] `cathaybot/config.py` 全局配置加载器
  - [ ] `cathaybot/utils/plugin_config.py` 插件配置基类
  - [ ] `configs/config.yaml` 全局配置文件
  - [ ] `configs/config.example.yaml` 配置模板

- [ ] 搭建数据库层
  - [ ] `cathaybot/database/connection.py` 连接管理
  - [ ] `cathaybot/database/models.py` 基础模型
  - [ ] `cathaybot/database/crud.py` 通用 CRUD

- [ ] 更新入口文件
  - [ ] `bot.py` 添加数据库初始化
  - [ ] 添加配置加载逻辑

### Phase 2: 核心插件

- [ ] Help 插件
  - [ ] 插件扫描逻辑
  - [ ] 分类显示
  - [ ] 详情查询

- [ ] Statistics 插件
  - [ ] 消息记录模型
  - [ ] 命令记录模型
  - [ ] 统计查询命令
  - [ ] 数据清理任务

- [ ] Admin 插件
  - [ ] 状态查询
  - [ ] 插件管理
  - [ ] 广播功能
  - [ ] 用户封禁

### Phase 3: WebUI 插件

- [ ] 后端 API
  - [ ] 认证系统 (JWT)
  - [ ] 仪表盘数据接口
  - [ ] 插件管理接口
  - [ ] 日志查询接口

- [ ] 前端界面
  - [ ] Vue3 项目搭建
  - [ ] 登录页面
  - [ ] 仪表盘页面
  - [ ] 插件管理页面
  - [ ] 日志查看页面

- [ ] 打包发布
  - [ ] 前端构建脚本
  - [ ] PyPI 发布配置

### Phase 4: Web QQ 插件

- [ ] 消息存储
  - [ ] 消息监听与存储
  - [ ] 会话管理
  - [ ] 图片下载与存储

- [ ] API 开发
  - [ ] 会话列表接口
  - [ ] 消息历史接口
  - [ ] 图片服务接口
  - [ ] 搜索接口

- [ ] 前端界面
  - [ ] 会话列表组件
  - [ ] 聊天记录组件
  - [ ] 图片预览组件
  - [ ] 表情包管理

- [ ] 高级功能
  - [ ] 全文搜索
  - [ ] 消息导出
  - [ ] 表情包收藏

---

## 开发命令

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行机器人
python bot.py

# 运行测试
pytest

# 代码格式化
black cathaybot plugins
isort cathaybot plugins

# 类型检查
mypy cathaybot plugins

# 构建 WebUI 前端
cd plugins/webui/frontend
npm install
npm run build
```

---

## 注意事项

1. **异步优先**: 所有数据库操作使用异步方式
2. **类型安全**: 使用 Pydantic 验证所有配置和输入
3. **错误处理**: 捕获异常，避免插件崩溃影响整体
4. **日志记录**: 关键操作记录日志，便于调试
5. **数据安全**: 敏感数据加密存储，访问需要认证
