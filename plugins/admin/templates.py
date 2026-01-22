"""
Admin 插件 HTML 模板
"""

STATUS_TEMPLATE = """
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
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 20px;
            min-width: 420px;
        }
        .container {
            background: rgba(255,255,255,0.95);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid #f0f0f0;
        }
        .avatar {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            margin-right: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: white;
        }
        .header-info h1 {
            font-size: 22px;
            color: #333;
            margin-bottom: 4px;
        }
        .header-info .status {
            display: inline-flex;
            align-items: center;
            font-size: 14px;
            color: #52c41a;
        }
        .header-info .status::before {
            content: "";
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #52c41a;
            margin-right: 6px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }
        .stat-card .value {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-card .label {
            font-size: 12px;
            color: #888;
            margin-top: 4px;
        }
        .info-list {
            list-style: none;
        }
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .info-item:last-child {
            border-bottom: none;
        }
        .info-item .label {
            color: #888;
            font-size: 14px;
        }
        .info-item .value {
            color: #333;
            font-size: 14px;
            font-weight: 500;
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
            <div class="avatar">🤖</div>
            <div class="header-info">
                <h1>{{ bot_name }}</h1>
                <span class="status">运行中</span>
            </div>
        </div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{{ groups }}</div>
                <div class="label">群聊数量</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ friends }}</div>
                <div class="label">好友数量</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ plugins }}</div>
                <div class="label">已加载插件</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ uptime }}</div>
                <div class="label">运行时间</div>
            </div>
        </div>
        <ul class="info-list">
            <li class="info-item">
                <span class="label">机器人 QQ</span>
                <span class="value">{{ bot_id }}</span>
            </li>
            <li class="info-item">
                <span class="label">NoneBot 版本</span>
                <span class="value">{{ nonebot_version }}</span>
            </li>
            <li class="info-item">
                <span class="label">Python 版本</span>
                <span class="value">{{ python_version }}</span>
            </li>
            <li class="info-item">
                <span class="label">系统平台</span>
                <span class="value">{{ platform }}</span>
            </li>
        </ul>
        <div class="footer">
            CathayBot Admin · {{ time }}
        </div>
    </div>
</body>
</html>
"""

PLUGIN_LIST_TEMPLATE = """
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
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 20px;
            min-width: 450px;
        }
        .container {
            background: rgba(255,255,255,0.95);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid #f0f0f0;
        }
        .header h1 {
            font-size: 22px;
            color: #333;
        }
        .plugin-list {
            list-style: none;
        }
        .plugin-item {
            display: flex;
            align-items: center;
            padding: 12px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .plugin-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 12px;
        }
        .plugin-status.enabled { background: #52c41a; }
        .plugin-status.disabled { background: #ff4d4f; }
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
        .plugin-version {
            font-size: 12px;
            color: #667eea;
            background: #f0f0ff;
            padding: 2px 8px;
            border-radius: 10px;
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
            <h1>📦 插件列表</h1>
        </div>
        <ul class="plugin-list">
            {% for plugin in plugins %}
            <li class="plugin-item">
                <div class="plugin-status {{ 'enabled' if plugin.enabled else 'disabled' }}"></div>
                <div class="plugin-info">
                    <div class="plugin-name">{{ plugin.name }}</div>
                    <div class="plugin-desc">{{ plugin.description }}</div>
                </div>
                <span class="plugin-version">v{{ plugin.version }}</span>
            </li>
            {% endfor %}
        </ul>
        <div class="footer">
            共 {{ plugins|length }} 个插件 · {{ time }}
        </div>
    </div>
</body>
</html>
"""
