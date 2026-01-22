# CathayBot

<div align="center">

基于 NoneBot2 的高度插件化 QQ 机器人框架

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![NoneBot](https://img.shields.io/badge/nonebot-2.3.0+-red.svg)](https://nonebot.dev/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)

</div>

## 特性

- 🔌 **高度插件化** - 模块化设计，插件独立配置与管理
- ⚙️ **灵活配置** - YAML + Pydantic2 类型安全配置系统
- 📊 **数据统计** - 群发言统计、插件调用分析
- 🎨 **WebUI 管理** - 可视化管理面板（独立插件）
- 💬 **Web QQ** - 基于聊天记录的 Web 版 QQ 体验
- 🛠️ **管理工具** - 完善的管理员命令系统

## 快速开始

### 环境要求

- Python 3.10+
- pip / poetry

### 安装

```bash
# 克隆项目
git clone https://github.com/cg8-5712/CathayBot.git
cd CathayBot

# 安装依赖
pip install -r requirements.txt
# 或使用 poetry
poetry install

# 配置机器人
cp configs/config.example.yaml configs/config.yaml
# 编辑 configs/config.yaml，填入你的配置
```

### 配置

编辑 `configs/config.yaml`：

```yaml
bot:
  superusers: ["123456789"]    # 你的 QQ 号
  nickname: ["CathayBot"]
  command_start: ["/", "!"]

database:
  type: sqlite
  path: ./data/db.sqlite
```

编辑 `.env.dev`：

```env
HOST=127.0.0.1
PORT=8080
LOG_LEVEL=DEBUG
```

### 运行

```bash
# 开发模式
python bot.py

# 或使用 nb-cli
nb run
```

## 项目结构

```
CathayBot/
├── bot.py                    # 入口文件
├── pyproject.toml            # 项目依赖
├── configs/                  # 配置目录
│   ├── config.yaml           # 全局配置
│   └── plugins/              # 插件配置
├── cathaybot/                # 核心模块
│   ├── config.py             # 配置加载器
│   ├── database/             # 数据库层
│   └── utils/                # 工具函数
├── plugins/                  # 插件目录
│   ├── help/                 # 帮助插件
│   ├── statistics/           # 统计插件
│   ├── admin/                # 管理插件
│   ├── webui/                # WebUI 插件
│   └── web_qq/               # Web QQ 插件
├── data/                     # 数据存储
└── logs/                     # 日志目录
```

## 核心插件

### Help - 自动帮助生成

自动扫描所有插件，生成帮助信息。

```
/help              # 显示所有插件
/help <插件名>      # 显示插件详情
```

### Statistics - 数据统计

统计群发言次数、插件调用次数。

```
/stat today        # 今日统计
/stat week         # 本周统计
/stat user @xxx    # 用户统计
/stat plugin       # 插件调用排行
```

### Admin - 管理命令

管理员专用命令（需要超级管理员权限）。

```
/admin reload <插件>        # 重载插件
/admin enable <插件>        # 启用插件
/admin disable <插件>       # 禁用插件
/admin broadcast <消息>     # 群发消息
/admin status              # 机器人状态
```

### WebUI - Web 管理面板

可视化管理界面，支持：
- 仪表盘与数据可视化
- 插件管理
- 日志查看
- 配置编辑

访问：`http://localhost:8081`（默认端口）

### Web QQ - Web 版 QQ

基于聊天记录的 Web 版 QQ 体验：
- 实时消息存储
- 图片/表情包管理
- 分群聊天记录浏览
- 全文搜索
- 仿 QQ 界面

## 插件开发

### 创建插件

```python
# plugins/my_plugin/__init__.py
from nonebot import on_command
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="我的插件",
    description="插件描述",
    usage="/mycommand - 命令说明",
    type="application",
    config=None,
    extra={
        "author": "你的名字",
        "version": "1.0.0",
        "category": "工具",
    }
)

my_cmd = on_command("mycommand")

@my_cmd.handle()
async def handle():
    await my_cmd.finish("Hello World!")
```

### 插件配置

```python
# plugins/my_plugin/config.py
from pydantic import BaseModel

class Config(BaseModel):
    enabled: bool = True
    some_option: str = "default"
```

```yaml
# configs/plugins/my_plugin.yaml
enabled: true
some_option: "custom value"
```

详细开发指南请参考 [DEVELOPMENT.md](DEVELOPMENT.md)

## 部署

### Docker 部署

```bash
# 构建镜像
docker build -t cathaybot .

# 运行容器
docker run -d \
  --name cathaybot \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/data:/app/data \
  -p 8080:8080 \
  cathaybot
```

### 生产环境

```bash
# 使用生产配置
export ENVIRONMENT=prod

# 使用进程管理器
pm2 start bot.py --name cathaybot --interpreter python3
```

## 文档

- [开发指南](DEVELOPMENT.md) - 详细的开发文档
- [架构设计](claude.md) - 项目架构与设计思路
- [插件开发](docs/plugin-dev.md) - 插件开发教程
- [API 文档](docs/api.md) - WebUI API 文档

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 许可证。

## 致谢

- [NoneBot2](https://nonebot.dev/) - 优秀的 Python 机器人框架
- [OneBot](https://onebot.dev/) - 聊天机器人应用接口标准

## 联系方式

- Issue: [GitHub Issues](https://github.com/cg8-5712/CathayBot/issues)
- Email: 5712.cg8@gmail.com

---

<div align="center">
Made with ❤️ by <a href="https://github.com/cg8-5712">cg8-5712</a>
</div>
