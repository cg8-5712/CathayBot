"""
Whois 插件 HTML 模板
"""

WHOIS_TEMPLATE = """
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
            font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            max-width: 600px;
        }

        .header {
            text-align: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid #f0f0f0;
        }

        .header h1 {
            font-size: 24px;
            color: #333;
            margin-bottom: 8px;
        }

        .domain {
            font-size: 20px;
            color: #667eea;
            font-weight: bold;
            margin-bottom: 4px;
        }

        .timestamp {
            font-size: 12px;
            color: #999;
        }

        .section {
            margin-bottom: 20px;
        }

        .section-title {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 12px;
            padding-left: 12px;
            border-left: 4px solid #667eea;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .info-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
        }

        .info-item.full-width {
            grid-column: 1 / -1;
        }

        .info-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 4px;
        }

        .info-value {
            font-size: 14px;
            color: #333;
            font-weight: 500;
            word-break: break-all;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }

        .status-active {
            background: #d4edda;
            color: #155724;
        }

        .status-warning {
            background: #fff3cd;
            color: #856404;
        }

        .days-left {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 8px;
        }

        .days-left.good {
            background: #d4edda;
            color: #155724;
        }

        .days-left.warning {
            background: #fff3cd;
            color: #856404;
        }

        .days-left.danger {
            background: #f8d7da;
            color: #721c24;
        }

        .list-item {
            background: #f8f9fa;
            padding: 10px 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 13px;
            color: #333;
        }

        .ip-item {
            background: #e7f3ff;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
        }

        .ip-address {
            font-size: 15px;
            font-weight: bold;
            color: #0066cc;
            margin-bottom: 6px;
        }

        .ip-location {
            font-size: 13px;
            color: #666;
            margin-bottom: 4px;
        }

        .ip-isp {
            font-size: 12px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 域名信息查询</h1>
            <div class="domain">{{ whois.domain }}</div>
            <div class="timestamp">{{ time }}</div>
        </div>

        {% if whois.error %}
        <div class="section">
            <div class="info-item full-width">
                <div class="info-value" style="color: #dc3545;">❌ {{ whois.error }}</div>
            </div>
        </div>
        {% else %}

        <!-- 基本信息 -->
        <div class="section">
            <div class="section-title">📋 基本信息</div>
            <div class="info-grid">
                <div class="info-item full-width">
                    <div class="info-label">状态</div>
                    <div class="info-value">
                        <span class="status-badge status-active">{{ whois.status }}</span>
                    </div>
                </div>
                <div class="info-item full-width">
                    <div class="info-label">注册商</div>
                    <div class="info-value">{{ whois.registrar }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">组织</div>
                    <div class="info-value">{{ whois.org }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">国家</div>
                    <div class="info-value">{{ whois.country }}</div>
                </div>
            </div>
        </div>

        <!-- 时间信息 -->
        <div class="section">
            <div class="section-title">⏰ 时间信息</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">注册时间</div>
                    <div class="info-value">{{ whois.creation_date }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">更新时间</div>
                    <div class="info-value">{{ whois.updated_date }}</div>
                </div>
                <div class="info-item full-width">
                    <div class="info-label">过期时间</div>
                    <div class="info-value">
                        {{ whois.expiration_date }}
                        {% if whois.days_left is not none %}
                            {% if whois.days_left > 90 %}
                                <span class="days-left good">剩余 {{ whois.days_left }} 天</span>
                            {% elif whois.days_left > 30 %}
                                <span class="days-left warning">剩余 {{ whois.days_left }} 天</span>
                            {% elif whois.days_left > 0 %}
                                <span class="days-left danger">剩余 {{ whois.days_left }} 天</span>
                            {% else %}
                                <span class="days-left danger">已过期 {{ whois.days_left|abs }} 天</span>
                            {% endif %}
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>

        <!-- DNS 服务器 -->
        {% if whois.name_servers %}
        <div class="section">
            <div class="section-title">🖥️ DNS 服务器</div>
            {% for ns in whois.name_servers %}
            <div class="list-item">{{ ns }}</div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- DNS 解析 -->
        {% if dns %}
        <div class="section">
            <div class="section-title">🔍 DNS 解析</div>
            {% for ip in dns %}
            <div class="ip-item">
                <div class="ip-address">{{ ip }}</div>
                {% if ip in ip_locations %}
                <div class="ip-location">📍 {{ ip_locations[ip].country }} {{ ip_locations[ip].region }} {{ ip_locations[ip].city }}</div>
                <div class="ip-isp">🏢 {{ ip_locations[ip].isp }}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% endif %}
    </div>
</body>
</html>
"""
