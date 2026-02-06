"""
数据库模块使用示例

演示如何使用 cathaybot.database 模块的各种功能。
"""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from cathaybot.database import (
    # 模型基类
    BaseModel,
    SoftDeleteModel,
    # CRUD 操作
    CRUDBase,
    SoftDeleteCRUD,
    # 分页
    Paginator,
    SoftDeletePaginator,
    # 查询构建器
    QueryBuilder,
    SoftDeleteQueryBuilder,
    # 工具函数
    exists,
    get_or_create,
    update_or_create,
    get_recent,
    increment,
    # 连接管理
    get_session,
    init_db,
)


# ==================== 定义模型 ====================

class User(BaseModel):
    """用户模型（普通模型）"""

    __tablename__ = "example_users"

    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")


class Article(SoftDeleteModel):
    """文章模型（支持软删除）"""

    __tablename__ = "example_articles"

    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(Integer)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")


# ==================== 创建 CRUD 实例 ====================

user_crud = CRUDBase(User)
article_crud = SoftDeleteCRUD(Article)


# ==================== 示例函数 ====================

async def example_basic_crud():
    """示例 1：基础 CRUD 操作"""
    print("\n=== 示例 1：基础 CRUD 操作 ===")

    async with get_session() as session:
        # 创建用户
        user = await user_crud.create(
            session,
            username="alice",
            email="alice@example.com",
            age=25,
            status="active"
        )
        print(f"创建用户: {user.username} (ID: {user.id})")

        # 查询用户
        user = await user_crud.get(session, id=user.id)
        print(f"查询用户: {user.username}")

        # 更新用户
        await user_crud.update(session, id=user.id, age=26)
        print(f"更新用户年龄: {user.age} -> 26")

        # 查询多个用户
        users = await user_crud.get_multi(session, limit=10)
        print(f"查询到 {len(users)} 个用户")


async def example_bulk_operations():
    """示例 2：批量操作"""
    print("\n=== 示例 2：批量操作 ===")

    async with get_session() as session:
        # 批量创建用户
        users_data = [
            {"username": f"user{i}", "email": f"user{i}@example.com", "age": 20 + i}
            for i in range(1, 11)
        ]
        users = await user_crud.bulk_create(session, users_data)
        print(f"批量创建了 {len(users)} 个用户")

        # 批量更新
        updates = [
            {"id": user.id, "status": "active"}
            for user in users[:5]
        ]
        count = await user_crud.bulk_update(session, updates)
        print(f"批量更新了 {count} 个用户")


async def example_soft_delete():
    """示例 3：软删除操作"""
    print("\n=== 示例 3：软删除操作 ===")

    async with get_session() as session:
        # 创建文章
        article = await article_crud.create(
            session,
            title="测试文章",
            content="这是一篇测试文章",
            author_id=1,
            status="published"
        )
        print(f"创建文章: {article.title} (ID: {article.id})")

        # 软删除文章
        success = await article_crud.soft_delete(session, id=article.id)
        print(f"软删除文章: {'成功' if success else '失败'}")

        # 查询时自动过滤已删除记录
        articles = await article_crud.get_multi(session, include_deleted=False)
        print(f"查询未删除的文章: {len(articles)} 篇")

        # 包含已删除记录
        all_articles = await article_crud.get_multi(session, include_deleted=True)
        print(f"查询所有文章（包含已删除）: {len(all_articles)} 篇")

        # 恢复文章
        success = await article_crud.restore(session, id=article.id)
        print(f"恢复文章: {'成功' if success else '失败'}")


async def example_pagination():
    """示例 4：分页查询"""
    print("\n=== 示例 4：分页查询 ===")

    async with get_session() as session:
        # 创建测试数据
        users_data = [
            {"username": f"page_user{i}", "email": f"page{i}@example.com", "age": 20 + i}
            for i in range(1, 51)
        ]
        await user_crud.bulk_create(session, users_data)

        # 分页查询
        paginator = Paginator(User)
        page = await paginator.paginate(
            session,
            page=1,
            page_size=10,
            order_by="created_at",
            desc=True
        )

        print(f"总记录数: {page.total}")
        print(f"总页数: {page.total_pages}")
        print(f"当前页: {page.page}")
        print(f"当前页记录数: {len(page.items)}")
        print(f"是否有下一页: {page.has_next}")
        print(f"是否有上一页: {page.has_prev}")


async def example_query_builder():
    """示例 5：查询构建器"""
    print("\n=== 示例 5：查询构建器 ===")

    async with get_session() as session:
        # 创建测试数据
        users_data = [
            {"username": "admin1", "email": "admin1@example.com", "age": 30, "status": "active"},
            {"username": "admin2", "email": "admin2@example.com", "age": 25, "status": "active"},
            {"username": "user1", "email": "user1@example.com", "age": 20, "status": "inactive"},
            {"username": "user2", "email": "user2@example.com", "age": 35, "status": "active"},
        ]
        await user_crud.bulk_create(session, users_data)

        # 简单查询
        builder = QueryBuilder(User)
        users = await builder.filter(status="active").all(session)
        print(f"活跃用户数: {len(users)}")

        # 复杂查询
        users = await (
            QueryBuilder(User)
            .filter(status="active")
            .gt(age=25)
            .like(username="%admin%")
            .order_by("age", desc=True)
            .all(session)
        )
        print(f"符合条件的用户: {[u.username for u in users]}")

        # 统计查询
        count = await (
            QueryBuilder(User)
            .filter(status="active")
            .gt(age=20)
            .count(session)
        )
        print(f"年龄大于20的活跃用户数: {count}")

        # 检查是否存在
        exists_result = await (
            QueryBuilder(User)
            .filter(username="admin1")
            .exists(session)
        )
        print(f"用户 admin1 是否存在: {exists_result}")


async def example_utils():
    """示例 6：工具函数"""
    print("\n=== 示例 6：工具函数 ===")

    async with get_session() as session:
        # get_or_create
        user, created = await get_or_create(
            session,
            User,
            defaults={"email": "bob@example.com", "age": 28},
            username="bob"
        )
        print(f"get_or_create: {'创建' if created else '已存在'} - {user.username}")

        # update_or_create
        user, created = await update_or_create(
            session,
            User,
            defaults={"email": "bob_new@example.com", "age": 29},
            username="bob"
        )
        print(f"update_or_create: {'创建' if created else '更新'} - {user.email}")

        # exists
        exists_result = await exists(session, User, username="bob")
        print(f"用户 bob 是否存在: {exists_result}")

        # get_recent
        recent_users = await get_recent(session, User, limit=5)
        print(f"最近 5 个用户: {[u.username for u in recent_users]}")

        # increment（增加文章浏览次数）
        article = await article_crud.create(
            session,
            title="热门文章",
            content="内容",
            author_id=1
        )
        article = await increment(session, Article, id=article.id, field="view_count")
        print(f"文章浏览次数: {article.view_count}")


async def example_advanced_query():
    """示例 7：高级查询"""
    print("\n=== 示例 7：高级查询 ===")

    async with get_session() as session:
        # OR 条件查询
        users = await (
            QueryBuilder(User)
            .or_(
                QueryBuilder(User).filter(status="active"),
                QueryBuilder(User).like(username="%admin%")
            )
            .all(session)
        )
        print(f"活跃用户或管理员: {len(users)} 个")

        # 范围查询
        users = await (
            QueryBuilder(User)
            .between(age=(20, 30))
            .all(session)
        )
        print(f"年龄在 20-30 之间的用户: {len(users)} 个")

        # IN 查询
        users = await (
            QueryBuilder(User)
            .in_(status=["active", "pending"])
            .all(session)
        )
        print(f"状态为 active 或 pending 的用户: {len(users)} 个")

        # 组合查询
        users = await (
            QueryBuilder(User)
            .filter(status="active")
            .gt(age=20)
            .is_not_null("email")
            .order_by("created_at", desc=True)
            .limit(10)
            .all(session)
        )
        print(f"复杂条件查询结果: {len(users)} 个")


async def main():
    """主函数"""
    print("CathayBot 数据库模块使用示例")
    print("=" * 50)

    # 初始化数据库
    await init_db()
    print("数据库初始化完成")

    # 运行示例
    await example_basic_crud()
    await example_bulk_operations()
    await example_soft_delete()
    await example_pagination()
    await example_query_builder()
    await example_utils()
    await example_advanced_query()

    print("\n" + "=" * 50)
    print("所有示例运行完成！")


if __name__ == "__main__":
    asyncio.run(main())
