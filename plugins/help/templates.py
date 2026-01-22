"""
Help 插件 HTML 模板
"""

HELP_LIST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%);
            padding: 20px;
            min-width: 420px;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid #f0f0f0;
        }
        .header h1 {
            font-size: 24px;
            color: #333;
            margin-bottom: 8px;
        }
        .header .subtitle {
            font-size: 14px;
            color: #888;
        }
        .category {
            margin-bottom: 16px;
        }
        .category-title {
            font-size: 14px;
            font-weight: bold;
            color: #667eea;
            padding: 8px 12px;
            background: linear-gradient(90deg, #f0f0ff 0%, transparent 100%);
            border-left: 3px solid #667eea;
            margin-bottom: 8px;
        }
        .plugin-list {
            list-style: none;
            padding-left: 12px;
        }
        .plugin-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            margin-bottom: 6px;
            background: #f8f9fa;
            border-radius: 8px;
            transition: all 0.2s;
        }
        .plugin-item:hover {
            background: #f0f0f0;
            transform: translateX(4px);
        }
        .plugin-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            font-size: 16px;
        }
        .plugin-info {
            flex: 1;
        }
        .plugin-name {
            font-size: 15px;
            font-weight: 500;
            color: #333;
        }
        .plugin-desc {
            font-size: 12px;
            color: #888;
            margin-top: 2px;
        }
        .footer {
            text-align: center;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #f0f0f0;
            font-size: 12px;
            color: #aaa;
        }
        .tip {
            background: #fff7e6;
            border: 1px solid #ffd591;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            color: #d46b08;
            margin-top: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 帮助菜单</h1>
            <div class="subtitle">共 {{ total }} 个插件</div>
        </div>
        {% for category, plugins in categories.items() %}
        <div class="category">
            <div class="category-title">{{ category }}</div>
            <ul class="plugin-list">
                {% for plugin in plugins %}
                <li class="plugin-item">
                    <div class="plugin-icon">{{ plugin.icon }}</div>
                    <div class="plugin-info">
                        <div class="plugin-name">{{ plugin.name }}</div>
                        <div class="plugin-desc">{{ plugin.description }}</div>
                    </div>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endfor %}
        <div class="tip">
            💡 使用 /help &lt;插件名&gt; 查看详细用法
        </div>
        <div class="footer">
            CathayBot · {{ time }}
        </div>
    </div>
</body>
</html>
"""

HELP_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-width: 400px;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid #f0f0f0;
        }
        .icon {
            width: 56px;
            height: 56px;
            border-radius: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            font-size: 28px;
        }
        .header-info h1 {
            font-size: 22px;
            color: #333;
            margin-bottom: 4px;
        }
        .header-info .meta {
            font-size: 12px;
            color: #888;
        }
        .header-info .meta span {
            margin-right: 12px;
        }
        .section {
            margin-bottom: 16px;
        }
        .section-title {
            font-size: 14px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }
        .description {
            font-size: 14px;
            color: #555;
            line-height: 1.6;
        }
        .usage {
            background: #1a1a2e;
            border-radius: 8px;
            padding: 14px;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 13px;
            color: #a0e0a0;
            line-height: 1.8;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        .footer {
            text-align: center;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #f0f0f0;
            font-size: 12px;
            color: #aaa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">{{ icon }}</div>
            <div class="header-info">
                <h1>{{ name }}</h1>
                <div class="meta">
                    <span>v{{ version }}</span>
                    <span>by {{ author }}</span>
                    <span>{{ category }}</span>
                </div>
            </div>
        </div>
        <div class="section">
            <div class="section-title">📝 描述</div>
            <div class="description">{{ description }}</div>
        </div>
        <div class="section">
            <div class="section-title">📋 用法</div>
            <div class="usage">{{ usage }}</div>
        </div>
        <div class="footer">
            CathayBot · {{ time }}
        </div>
    </div>
</body>
</html>
"""

# 分类图标映射
CATEGORY_ICONS = {
    "工具": "🔧",
    "管理": "⚙️",
    "娱乐": "🎮",
    "其他": "📦",
}
