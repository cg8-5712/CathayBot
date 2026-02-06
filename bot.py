"""
CathayBot - 高度插件化 NoneBot2 QQ 机器人

入口文件
"""

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# 初始化 NoneBot
nonebot.init()

# 获取驱动器并注册适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)


@driver.on_startup
async def startup():
    """应用启动时初始化数据库和 Redis"""
    from cathaybot.database import init_db
    from cathaybot.cache import init_redis

    await init_db()
    await init_redis()


@driver.on_shutdown
async def shutdown():
    """应用关闭时清理资源"""
    from cathaybot.database import close_db
    from cathaybot.cache import close_redis

    await close_redis()
    await close_db()


# 加载插件
nonebot.load_plugins("plugins")

# 获取 ASGI 应用 (用于 WebUI 等)
# app = nonebot.get_asgi()

if __name__ == "__main__":
    nonebot.run()