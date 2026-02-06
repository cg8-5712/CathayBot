"""
Statistics 插件 HTML 模板
"""

# 排行榜模板（用于 today/week/month/all）
RANK_TEMPLATE = """
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
        .rank-list {
            list-style: none;
        }
        .rank-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 12px;
            transition: transform 0.2s;
        }
        .rank-item:hover {
            transform: translateX(4px);
        }
        .rank-num {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            margin-right: 12px;
        }
        .rank-1 .rank-num { background: linear-gradient(135deg, #FFD700, #FFA500); color: white; }
        .rank-2 .rank-num { background: linear-gradient(135deg, #C0C0C0, #A0A0A0); color: white; }
        .rank-3 .rank-num { background: linear-gradient(135deg, #CD7F32, #8B4513); color: white; }
        .rank-other .rank-num { background: #e0e0e0; color: #666; }
        .rank-info {
            flex: 1;
        }
        .rank-name {
            font-size: 16px;
            font-weight: 500;
            color: #333;
        }
        .rank-detail {
            font-size: 12px;
            color: #888;
            margin-top: 2px;
        }
        .rank-count {
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
        }
        .footer {
            text-align: center;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #f0f0f0;
            font-size: 12px;
            color: #aaa;
        }
        .empty {
            text-align: center;
            padding: 40px;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="subtitle">{{ subtitle }}</div>
        </div>
        {% if items %}
        <ul class="rank-list">
            {% for item in items %}
            <li class="rank-item {% if loop.index <= 3 %}rank-{{ loop.index }}{% else %}rank-other{% endif %}">
                <div class="rank-num">{{ loop.index }}</div>
                <div class="rank-info">
                    <div class="rank-name">{{ item.name }}</div>
                    {% if item.detail %}
                    <div class="rank-detail">{{ item.detail }}</div>
                    {% endif %}
                </div>
                <div class="rank-count">{{ item.count }}</div>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <div class="empty">暂无数据</div>
        {% endif %}
        <div class="footer">
            CathayBot Statistics · {{ time }}
        </div>
    </div>
</body>
</html>
"""

# 用户统计模板
USER_STAT_TEMPLATE = """
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
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        .stat-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
        }
        .stat-card.highlight {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            grid-column: span 2;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
        }
        .stat-card.highlight .stat-label {
            color: rgba(255,255,255,0.9);
        }
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-card.highlight .stat-value {
            color: white;
            font-size: 32px;
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
            <h1>{{ title }}</h1>
            <div class="subtitle">{{ subtitle }}</div>
        </div>
        <div class="stats-grid">
            {% for item in items %}
            <div class="stat-card {% if item.name == '总发言' %}highlight{% endif %}">
                <div class="stat-label">{{ item.name }}</div>
                <div class="stat-value">{{ item.count }}</div>
            </div>
            {% endfor %}
        </div>
        <div class="footer">
            CathayBot Statistics · {{ time }}
        </div>
    </div>
</body>
</html>
"""

# 插件统计模板
PLUGIN_STAT_TEMPLATE = """
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
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
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
        .plugin-list {
            list-style: none;
        }
        .plugin-item {
            display: flex;
            align-items: center;
            padding: 14px 16px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #11998e;
            transition: all 0.2s;
        }
        .plugin-item:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .plugin-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-right: 12px;
        }
        .plugin-info {
            flex: 1;
        }
        .plugin-name {
            font-size: 16px;
            font-weight: 500;
            color: #333;
        }
        .plugin-count {
            font-size: 20px;
            font-weight: bold;
            color: #11998e;
        }
        .plugin-count-label {
            font-size: 12px;
            color: #888;
            margin-left: 4px;
        }
        .footer {
            text-align: center;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #f0f0f0;
            font-size: 12px;
            color: #aaa;
        }
        .empty {
            text-align: center;
            padding: 40px;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="subtitle">{{ subtitle }}</div>
        </div>
        {% if items %}
        <ul class="plugin-list">
            {% for item in items %}
            <li class="plugin-item">
                <div class="plugin-icon">🔌</div>
                <div class="plugin-info">
                    <div class="plugin-name">{{ item.name }}</div>
                </div>
                <div>
                    <span class="plugin-count">{{ item.count }}</span>
                    <span class="plugin-count-label">次调用</span>
                </div>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <div class="empty">暂无数据</div>
        {% endif %}
        <div class="footer">
            CathayBot Statistics · {{ time }}
        </div>
    </div>
</body>
</html>
"""

# 保留旧的模板名称以兼容
STAT_TEMPLATE = RANK_TEMPLATE

