"""
Bilibili 视频卡片 HTML 模板
"""

VIDEO_CARD_TEMPLATE = """
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
            font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
            background: #f4f5f7;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        /* 视频标题 */
        .video-title {
            padding: 20px 24px 16px;
            font-size: 20px;
            font-weight: 600;
            color: #18191c;
            line-height: 1.4;
            border-bottom: 1px solid #e3e5e7;
        }

        /* 视频封面区域 */
        .video-cover {
            position: relative;
            width: 100%;
            background: #000;
        }

        .cover-img {
            width: 100%;
            display: block;
        }

        .duration-badge {
            position: absolute;
            bottom: 12px;
            right: 12px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }

        /* 视频信息区 */
        .video-info {
            padding: 16px 24px;
        }

        /* UP主信息 */
        .uploader {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid #e3e5e7;
        }

        .uploader-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            margin-right: 12px;
            border: 2px solid #e3e5e7;
        }

        .uploader-info {
            flex: 1;
        }

        .uploader-name {
            font-size: 15px;
            font-weight: 600;
            color: #18191c;
            margin-bottom: 4px;
        }

        .video-category {
            display: inline-block;
            background: #e5f2ff;
            color: #00a1d6;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }

        /* 统计数据 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }

        .stat-item {
            text-align: center;
            padding: 12px;
            background: #f9fafb;
            border-radius: 6px;
        }

        .stat-icon {
            width: 20px;
            height: 20px;
            margin-bottom: 6px;
        }

        .stat-value {
            font-size: 16px;
            font-weight: 600;
            color: #18191c;
            margin-bottom: 2px;
        }

        .stat-label {
            font-size: 12px;
            color: #9499a0;
        }

        /* 图标颜色 */
        .icon-play { color: #00a1d6; }
        .icon-danmaku { color: #fb7299; }
        .icon-like { color: #ff6699; }
        .icon-coin { color: #ffb11b; }
        .icon-fav { color: #ff9500; }
        .icon-share { color: #00c7ae; }

        /* 视频简介 */
        .video-desc {
            padding: 16px;
            background: #f9fafb;
            border-radius: 6px;
            font-size: 14px;
            color: #61666d;
            line-height: 1.6;
        }

        .desc-title {
            font-weight: 600;
            color: #18191c;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 视频标题 -->
        <div class="video-title">{{ title }}</div>

        <!-- 视频封面 -->
        <div class="video-cover">
            <img class="cover-img" src="{{ cover }}" alt="视频封面">
            <div class="duration-badge">{{ duration }}</div>
        </div>

        <!-- 视频信息 -->
        <div class="video-info">
            <!-- UP主信息 -->
            <div class="uploader">
                <img class="uploader-avatar" src="{{ owner.face }}" alt="UP主头像">
                <div class="uploader-info">
                    <div class="uploader-name">{{ owner.name }}</div>
                    <span class="video-category">{{ tname }}</span>
                </div>
            </div>

            <!-- 统计数据 -->
            <div class="stats-grid">
                <div class="stat-item">
                    <svg class="stat-icon icon-play" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8 5v14l11-7z"/>
                    </svg>
                    <div class="stat-value">{{ stat.view }}</div>
                    <div class="stat-label">播放</div>
                </div>

                <div class="stat-item">
                    <svg class="stat-icon icon-danmaku" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
                    </svg>
                    <div class="stat-value">{{ stat.danmaku }}</div>
                    <div class="stat-label">弹幕</div>
                </div>

                <div class="stat-item">
                    <svg class="stat-icon icon-like" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/>
                    </svg>
                    <div class="stat-value">{{ stat.like }}</div>
                    <div class="stat-label">点赞</div>
                </div>

                <div class="stat-item">
                    <svg class="stat-icon icon-coin" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.31-8.86c-1.77-.45-2.34-.94-2.34-1.67 0-.84.79-1.43 2.1-1.43 1.38 0 1.9.66 1.94 1.64h1.71c-.05-1.34-.87-2.57-2.49-2.97V5H10.9v1.69c-1.51.32-2.72 1.3-2.72 2.81 0 1.79 1.49 2.69 3.66 3.21 1.95.46 2.34 1.15 2.34 1.87 0 .53-.39 1.39-2.1 1.39-1.6 0-2.23-.72-2.32-1.64H8.04c.1 1.7 1.36 2.66 2.86 2.97V19h2.34v-1.67c1.52-.29 2.72-1.16 2.73-2.77-.01-2.2-1.9-2.96-3.66-3.42z"/>
                    </svg>
                    <div class="stat-value">{{ stat.coin }}</div>
                    <div class="stat-label">投币</div>
                </div>
            </div>

            <!-- 视频简介 -->
            {% if desc %}
            <div class="video-desc">
                <div class="desc-title">简介</div>
                {{ desc }}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""
