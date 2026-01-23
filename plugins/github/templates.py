"""
GitHub 卡片 HTML 模板

参考 GitHub.Cards 风格设计
"""

# 用户卡片模板
USER_CARD_TEMPLATE = """
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background: #f6f8fa;
            padding: 16px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            width: 480px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.06);
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }
        .avatar {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            margin-right: 16px;
            border: 2px solid #e1e4e8;
        }
        .user-info h1 {
            font-size: 20px;
            font-weight: 600;
            color: #24292f;
            margin-bottom: 2px;
        }
        .user-info .username {
            font-size: 14px;
            color: #57606a;
        }
        .bio {
            font-size: 14px;
            color: #24292f;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 20px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        .stat-value.stars { color: #eab308; }
        .stat-value.forks { color: #8b5cf6; }
        .stat-value.followers { color: #ec4899; }
        .stat-value.commits { color: #6366f1; }
        .stat-value.prs { color: #22c55e; }
        .stat-value.repos { color: #3b82f6; }
        .stat-label {
            font-size: 12px;
            color: #57606a;
            margin-top: 2px;
        }
        .section {
            margin-bottom: 16px;
        }
        .section-title {
            font-size: 14px;
            font-weight: 600;
            color: #24292f;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .section-title svg {
            width: 16px;
            height: 16px;
        }
        .languages {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .lang-tag {
            font-size: 12px;
            padding: 4px 12px;
            background: #f3f4f6;
            border-radius: 16px;
            color: #374151;
            border: 1px solid #e5e7eb;
        }
        .repo-list {
            list-style: none;
        }
        .repo-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: #fdf2f8;
            border-radius: 8px;
            margin-bottom: 6px;
        }
        .repo-name {
            font-size: 14px;
            color: #db2777;
            font-weight: 500;
        }
        .repo-stats {
            display: flex;
            gap: 12px;
            font-size: 13px;
            color: #db2777;
        }
        .repo-stats span {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .footer {
            text-align: right;
            font-size: 11px;
            color: #9ca3af;
            margin-top: 12px;
        }
        /* SVG Icons */
        .icon-star { color: #eab308; }
        .icon-fork { color: #8b5cf6; }
        .icon-followers { color: #ec4899; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <img class="avatar" src="{{ avatar_url }}" alt="avatar">
            <div class="user-info">
                <h1>{{ name or login }}</h1>
                <div class="username">@{{ login }}</div>
            </div>
        </div>

        {% if bio %}
        <div class="bio">{{ bio }}</div>
        {% endif %}

        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value stars">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/>
                    </svg>
                    {{ total_stars }}
                </div>
                <div class="stat-label">Stars Earned</div>
            </div>
            <div class="stat-item">
                <div class="stat-value forks">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"/>
                    </svg>
                    {{ total_forks }}
                </div>
                <div class="stat-label">Total Forks</div>
            </div>
            <div class="stat-item">
                <div class="stat-value followers">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M2 5.5a3.5 3.5 0 115.898 2.549 5.507 5.507 0 013.034 4.084.75.75 0 11-1.482.235 4.001 4.001 0 00-7.9 0 .75.75 0 01-1.482-.236A5.507 5.507 0 013.102 8.05 3.49 3.49 0 012 5.5zM11 4a.75.75 0 100 1.5 1.5 1.5 0 01.666 2.844.75.75 0 00-.416.672v.352a.75.75 0 00.574.73c1.2.289 2.162 1.2 2.522 2.372a.75.75 0 101.434-.44 5.01 5.01 0 00-2.56-3.012A3 3 0 0011 4z"/>
                    </svg>
                    {{ followers }}
                </div>
                <div class="stat-label">Followers</div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value commits">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M11.93 8.5a4.002 4.002 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 010 1.5h-3.32zm-1.43-.75a2.5 2.5 0 10-5 0 2.5 2.5 0 005 0z"/>
                    </svg>
                    {{ total_commits or '-' }}
                </div>
                <div class="stat-label">Total Commits</div>
            </div>
            <div class="stat-item">
                <div class="stat-value prs">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M1.5 3.25a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zm5.677-.177L9.573.677A.25.25 0 0110 .854V2.5h1A2.5 2.5 0 0113.5 5v5.628a2.251 2.251 0 11-1.5 0V5a1 1 0 00-1-1h-1v1.646a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm0 9.5a.75.75 0 100 1.5.75.75 0 000-1.5zm8.25.75a.75.75 0 11-1.5 0 .75.75 0 011.5 0z"/>
                    </svg>
                    {{ total_prs or '-' }}
                </div>
                <div class="stat-label">Total PRs</div>
            </div>
            <div class="stat-item">
                <div class="stat-value repos">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
                    </svg>
                    {{ public_repos }}
                </div>
                <div class="stat-label">Repositories</div>
            </div>
        </div>

        {% if top_languages %}
        <div class="section">
            <div class="section-title">
                <svg viewBox="0 0 16 16" width="16" height="16" fill="#6366f1">
                    <path d="M0 1.75C0 .784.784 0 1.75 0h12.5C15.216 0 16 .784 16 1.75v12.5A1.75 1.75 0 0114.25 16H1.75A1.75 1.75 0 010 14.25V1.75zm1.75-.25a.25.25 0 00-.25.25v12.5c0 .138.112.25.25.25h12.5a.25.25 0 00.25-.25V1.75a.25.25 0 00-.25-.25H1.75zM7.25 8a.75.75 0 01-.22.53l-2.25 2.25a.75.75 0 11-1.06-1.06L5.44 8 3.72 6.28a.75.75 0 111.06-1.06l2.25 2.25c.141.14.22.331.22.53zm1.5 1.5a.75.75 0 000 1.5h3a.75.75 0 000-1.5h-3z"/>
                </svg>
                Top Languages
            </div>
            <div class="languages">
                {% for lang in top_languages %}
                <span class="lang-tag">{{ lang }}</span>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if top_repos %}
        <div class="section">
            <div class="section-title">
                <svg viewBox="0 0 16 16" width="16" height="16" fill="#db2777">
                    <path d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
                </svg>
                Most Popular Repositories
            </div>
            <ul class="repo-list">
                {% for repo in top_repos %}
                <li class="repo-item">
                    <span class="repo-name">{{ repo.name }}</span>
                    <div class="repo-stats">
                        <span>☆ {{ repo.stars }}</span>
                        <span>⑂ {{ repo.forks }}</span>
                    </div>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <div class="footer">CathayBot · GitHub</div>
    </div>
</body>
</html>
"""

# 仓库卡片模板
REPO_CARD_TEMPLATE = """
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background: #f6f8fa;
            padding: 16px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            width: 480px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.06);
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }
        .avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            margin-right: 12px;
            border: 2px solid #e1e4e8;
        }
        .repo-info h1 {
            font-size: 18px;
            font-weight: 600;
            color: #0969da;
            margin-bottom: 2px;
        }
        .repo-info .owner {
            font-size: 13px;
            color: #57606a;
        }
        .description {
            font-size: 14px;
            color: #24292f;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }
        .stat-value.stars { color: #eab308; }
        .stat-value.forks { color: #8b5cf6; }
        .stat-value.watchers { color: #3b82f6; }
        .stat-value.issues { color: #22c55e; }
        .stat-label {
            font-size: 11px;
            color: #57606a;
            margin-top: 2px;
        }
        .meta {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 16px;
        }
        .meta-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #57606a;
        }
        .meta-item svg {
            width: 14px;
            height: 14px;
        }
        .language-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #3178c6;
        }
        .topics {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
        }
        .topic-tag {
            font-size: 12px;
            padding: 4px 10px;
            background: #ddf4ff;
            border-radius: 16px;
            color: #0969da;
        }
        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #9ca3af;
            border-top: 1px solid #e5e7eb;
            padding-top: 12px;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <img class="avatar" src="{{ owner_avatar }}" alt="avatar">
            <div class="repo-info">
                <h1>{{ name }}</h1>
                <div class="owner">{{ owner_login }}</div>
            </div>
        </div>

        {% if description %}
        <div class="description">{{ description }}</div>
        {% else %}
        <div class="description" style="color: #9ca3af; font-style: italic;">No description provided</div>
        {% endif %}

        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value stars">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/>
                    </svg>
                    {{ stargazers_count }}
                </div>
                <div class="stat-label">Stars</div>
            </div>
            <div class="stat-item">
                <div class="stat-value forks">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"/>
                    </svg>
                    {{ forks_count }}
                </div>
                <div class="stat-label">Forks</div>
            </div>
            <div class="stat-item">
                <div class="stat-value watchers">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M8 2c1.981 0 3.671.992 4.933 2.078 1.27 1.091 2.187 2.345 2.637 3.023a1.62 1.62 0 010 1.798c-.45.678-1.367 1.932-2.637 3.023C11.67 13.008 9.981 14 8 14c-1.981 0-3.671-.992-4.933-2.078C1.797 10.83.88 9.576.43 8.898a1.62 1.62 0 010-1.798c.45-.677 1.367-1.931 2.637-3.022C4.33 2.992 6.019 2 8 2zM1.679 7.932a.12.12 0 000 .136c.411.622 1.241 1.75 2.366 2.717C5.176 11.758 6.527 12.5 8 12.5c1.473 0 2.825-.742 3.955-1.715 1.124-.967 1.954-2.096 2.366-2.717a.12.12 0 000-.136c-.412-.621-1.242-1.75-2.366-2.717C10.824 4.242 9.473 3.5 8 3.5c-1.473 0-2.824.742-3.955 1.715-1.124.967-1.954 2.096-2.366 2.717zM8 10a2 2 0 110-4 2 2 0 010 4z"/>
                    </svg>
                    {{ watchers_count }}
                </div>
                <div class="stat-label">Watchers</div>
            </div>
            <div class="stat-item">
                <div class="stat-value issues">
                    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
                        <path d="M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/>
                        <path d="M8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 1113 0 6.5 6.5 0 01-13 0z"/>
                    </svg>
                    {{ open_issues_count }}
                </div>
                <div class="stat-label">Issues</div>
            </div>
        </div>

        <div class="meta">
            {% if language %}
            <div class="meta-item">
                <span class="language-dot"></span>
                {{ language }}
            </div>
            {% endif %}
            {% if license_name %}
            <div class="meta-item">
                <svg viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8.75.75a.75.75 0 00-1.5 0V2h-.984c-.305 0-.604.08-.869.23l-1.288.737A.25.25 0 013.984 3H1.75a.75.75 0 000 1.5h.428L.066 9.192a.75.75 0 00.154.838l.53-.53-.53.53v.001l.002.002.002.002.006.006.016.015.045.04a3.514 3.514 0 00.686.45A4.492 4.492 0 003 11c.88 0 1.556-.22 2.023-.454a3.515 3.515 0 00.686-.45l.045-.04.016-.015.006-.006.002-.002.001-.002L5.25 9.5l.53.53a.75.75 0 00.154-.838L3.822 4.5h.162c.305 0 .604-.08.869-.23l1.289-.737a.25.25 0 01.124-.033h.984V13h-2.5a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-2.5V3.5h.984a.25.25 0 01.124.033l1.29.736c.264.152.563.231.868.231h.162l-2.112 4.692a.75.75 0 00.154.838l.53-.53-.53.53v.001l.002.002.002.002.006.006.016.015.045.04a3.517 3.517 0 00.686.45A4.492 4.492 0 0013 11c.88 0 1.556-.22 2.023-.454a3.512 3.512 0 00.686-.45l.045-.04.01-.01.006-.005.006-.006.002-.002.001-.002-.529-.531.53.53a.75.75 0 00.154-.838L13.823 4.5h.427a.75.75 0 000-1.5h-2.234a.25.25 0 01-.124-.033l-1.29-.736A1.75 1.75 0 009.735 2H8.75V.75zM1.695 9.227c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L3 6.327l-1.305 2.9zm10 0c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L13 6.327l-1.305 2.9z"/>
                </svg>
                {{ license_name }}
            </div>
            {% endif %}
        </div>

        {% if topics %}
        <div class="topics">
            {% for topic in topics[:6] %}
            <span class="topic-tag">{{ topic }}</span>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            <span>Updated: {{ updated_at[:10] }}</span>
            <span>CathayBot · GitHub</span>
        </div>
    </div>
</body>
</html>
"""
