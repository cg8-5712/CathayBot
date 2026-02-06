# CathayBot Dockerfile
# 多阶段构建，优化镜像大小

# ============================================
# 阶段 1: 基础镜像
# ============================================
FROM python:3.12-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 安装系统依赖和 Playwright 所需的库
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    wget \
    gnupg \
    # Playwright 浏览器依赖
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    # 字体支持
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# 阶段 2: 依赖安装
# ============================================
FROM base as builder

WORKDIR /build

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖到临时目录
RUN pip install --user --no-warn-script-location -r requirements.txt

# 安装 Playwright 浏览器
RUN python -m playwright install chromium

# ============================================
# 阶段 3: 运行时镜像
# ============================================
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 安装运行时依赖和 Playwright 所需的库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    # Playwright 浏览器运行时依赖
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    # 字体支持
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 创建应用目录
WORKDIR /app

# 从 builder 阶段复制已安装的依赖
COPY --from=builder /root/.local /root/.local

# 从 builder 阶段复制 Playwright 浏览器
COPY --from=builder /ms-playwright /ms-playwright

# 复制应用代码
COPY bot.py .
COPY cathaybot/ ./cathaybot/
COPY plugins/ ./plugins/
COPY configs/ ./configs/

# 创建数据和日志目录
RUN mkdir -p /app/data /app/logs /app/data/cache

# 暴露端口
# NoneBot2 默认端口 (可通过 .env 配置)
EXPOSE 8080
# WebUI 端口 (可通过配置文件修改)
EXPOSE 8081

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# 启动命令
CMD ["python", "bot.py"]
