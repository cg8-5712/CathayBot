# CathayBot 数据库模块使用指南

## 概述

CathayBot 数据库模块提供了完整的数据库操作功能，包括：

- 🔌 数据库连接管理（SQLite/PostgreSQL）
- 📦 模型基类和混入类
- 🔧 通用 CRUD 操作
- 🗑️ 软删除支持
- 📄 增强的分页功能
- 🔍 灵活的查询构建器

---

## 快速开始

### 1. 定义模型

```python
from cathaybot.database import BaseModel, SoftDeleteModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

# 普通模型（包含 id, created_at, updated_at）
class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100))

# 支持软删除的模型（额外包含 is_deleted, deleted_at）
class Post(SoftDeleteModel):
    __tablename__ = "posts"

    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(5000))
    user_id: Mapped[int] = mapped_column(Integer)
```

### 2. 使用 CRUD 操作

```python
from cathaybot.database import CRUDBase, SoftDeleteCRUD, get_session

# 创建 CRUD 实例
user_crud = CRUDBase(User)
post_crud = SoftDeleteCRUD(Post)

# 使用数据库会话
async with get_session() as session:
    # 创建记录
    user = await user_crud.create(
        session,
        username="alice",
        email="alice@example.com"
    )

    # 查询记录
    user = await user_crud.get(session, id=1)
    users = await user_crud.get_multi(session, limit=10)

    # 更新记录
    await user_crud.update(session, id=1, email="newemail@example.com")

    # 删除记录
    await user_crud.delete(session, id=1)
```

---

## 核心功能详解

### 一、模型基类

#### 1. BaseModel

包含基础字段：`id`, `created_at`, `updated_at`

```python
from cathaybot.database import BaseModel

class Article(BaseModel):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
```

#### 2. SoftDeleteModel

在 BaseModel 基础上增加软删除字段：`is_deleted`, `deleted_at`

```python
from cathaybot.database import SoftDeleteModel

class Comment(SoftDeleteModel):
    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(Text)
    article_id: Mapped[int] = mapped_column(Integer)
```

#### 3. 自定义混入

```python
from cathaybot.database import Base, IDMixin, TimestampMixin, SoftDeleteMixin

class CustomModel(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "custom"
    __abstract__ = True

    # 自定义字段
    custom_field: Mapped[str] = mapped_column(String(100))
```

---

### 二、CRUD 操作

#### 1. 基础 CRUD（CRUDBase）

```python
from cathaybot.database import CRUDBase, get_session

user_crud = CRUDBase(User)

async with get_session() as session:
    # 创建单条记录
    user = await user_crud.create(
        session,
        username="bob",
        email="bob@example.com"
    )

    # 根据 ID 查询
    user = await user_crud.get(session, id=1)

    # 根据条件查询
    user = await user_crud.get_by(session, username="bob")

    # 查询多条记录
    users = await user_crud.get_multi(
        session,
        offset=0,
        limit=10,
        order_by="created_at",
        desc=True,
        status="active"  # 过滤条件
    )

    # 统计数量
    count = await user_crud.count(session, status="active")

    # 更新记录
    user = await user_crud.update(
        session,
        id=1,
        email="newemail@example.com"
    )

    # 删除记录
    success = await user_crud.delete(session, id=1)

    # 根据条件删除
    deleted_count = await user_crud.delete_by(session, status="inactive")
```

#### 2. 批量操作

```python
async with get_session() as session:
    # 批量创建
    users = await user_crud.bulk_create(
        session,
        [
            {"username": "user1", "email": "user1@example.com"},
            {"username": "user2", "email": "user2@example.com"},
            {"username": "user3", "email": "user3@example.com"},
        ]
    )

    # 批量更新
    count = await user_crud.bulk_update(
        session,
        [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "active"},
            {"id": 3, "status": "inactive"},
        ]
    )

    # 批量删除
    count = await user_crud.bulk_delete(session, [1, 2, 3])
```

#### 3. 软删除 CRUD（SoftDeleteCRUD）

```python
from cathaybot.database import SoftDeleteCRUD

post_crud = SoftDeleteCRUD(Post)

async with get_session() as session:
    # 查询时自动过滤已删除记录
    posts = await post_crud.get_multi(session, include_deleted=False)

    # 包含已删除记录
    all_posts = await post_crud.get_multi(session, include_deleted=True)

    # 软删除（标记为已删除，不真正删除）
    success = await post_crud.soft_delete(session, id=1)

    # 根据条件软删除
    count = await post_crud.soft_delete_by(session, user_id=123)

    # 恢复已删除的记录
    success = await post_crud.restore(session, id=1)

    # 根据条件恢复
    count = await post_crud.restore_by(session, user_id=123)

    # 永久删除（物理删除）
    success = await post_crud.hard_delete(session, id=1)

    # 根据条件永久删除
    count = await post_crud.hard_delete_by(session, user_id=123)
```

---

### 三、分页功能

#### 1. 基础分页（Paginator）

```python
from cathaybot.database import Paginator, get_session

paginator = Paginator(User)

async with get_session() as session:
    # 基础分页
    page = await paginator.paginate(
        session,
        page=1,
        page_size=20
    )

    print(f"总记录数: {page.total}")
    print(f"总页数: {page.total_pages}")
    print(f"当前页: {page.page}")
    print(f"是否有下一页: {page.has_next}")
    print(f"是否有上一页: {page.has_prev}")

    for user in page.items:
        print(user.username)

    # 带过滤和排序的分页
    page = await paginator.paginate(
        session,
        page=2,
        page_size=10,
        filters={"status": "active"},
        order_by="created_at",
        desc=True
    )

    # 转换为字典
    page_dict = page.to_dict()
```

#### 2. 软删除分页（SoftDeletePaginator）

```python
from cathaybot.database import SoftDeletePaginator

paginator = SoftDeletePaginator(Post)

async with get_session() as session:
    # 默认不包含已删除记录
    page = await paginator.paginate(
        session,
        page=1,
        page_size=20
    )

    # 包含已删除记录
    page = await paginator.paginate(
        session,
        page=1,
        page_size=20,
        include_deleted=True
    )
```

---

### 四、查询构建器

#### 1. 基础查询（QueryBuilder）

```python
from cathaybot.database import QueryBuilder, get_session

builder = QueryBuilder(User)

async with get_session() as session:
    # 等值查询
    users = await builder.filter(status="active").all(session)

    # 模糊查询
    users = await (
        builder
        .like(username="%admin%")
        .all(session)
    )

    # IN 查询
    users = await (
        builder
        .in_(role=["admin", "moderator"])
        .all(session)
    )

    # 范围查询
    from datetime import datetime, timedelta
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    users = await (
        builder
        .between(created_at=(start_date, end_date))
        .all(session)
    )

    # 比较查询
    users = await (
        builder
        .gt(age=18)
        .lte(age=65)
        .all(session)
    )

    # NULL 查询
    users = await (
        builder
        .is_null("deleted_at")
        .all(session)
    )

    # 排序和限制
    users = await (
        builder
        .filter(status="active")
        .order_by("created_at", desc=True)
        .limit(10)
        .all(session)
    )
```

#### 2. 复杂查询

```python
async with get_session() as session:
    # 组合条件（AND）
    users = await (
        builder
        .filter(status="active")
        .gt(age=18)
        .like(username="%admin%")
        .all(session)
    )

    # OR 条件
    users = await (
        builder
        .or_(
            QueryBuilder(User).filter(status="active"),
            QueryBuilder(User).filter(role="admin")
        )
        .all(session)
    )

    # NOT 条件
    users = await (
        builder
        .not_(QueryBuilder(User).filter(status="banned"))
        .all(session)
    )

    # 复杂组合
    users = await (
        builder
        .filter(status="active")
        .or_(
            QueryBuilder(User).gt(age=18),
            QueryBuilder(User).filter(role="admin")
        )
        .order_by("created_at", desc=True)
        .limit(20)
        .all(session)
    )
```

#### 3. 查询方法

```python
async with get_session() as session:
    # 获取所有结果
    users = await builder.filter(status="active").all(session)

    # 获取第一条结果
    user = await builder.filter(username="alice").first(session)

    # 统计数量
    count = await builder.filter(status="active").count(session)

    # 检查是否存在
    exists = await builder.filter(username="alice").exists(session)
```

#### 4. 软删除查询（SoftDeleteQueryBuilder）

```python
from cathaybot.database import SoftDeleteQueryBuilder

builder = SoftDeleteQueryBuilder(Post)

async with get_session() as session:
    # 默认不包含已删除记录
    posts = await builder.filter(status="published").all(session)

    # 包含已删除记录
    posts = await (
        builder
        .include_deleted()
        .filter(status="published")
        .all(session)
    )

    # 只查询已删除记录
    posts = await (
        builder
        .only_deleted()
        .all(session)
    )
```

---

## 实际应用示例

### 示例 1：用户管理系统

```python
from cathaybot.database import BaseModel, CRUDBase, QueryBuilder, Paginator, get_session
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

# 定义模型
class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")

# 创建 CRUD 实例
user_crud = CRUDBase(User)

# 用户注册
async def register_user(username: str, email: str, age: int):
    async with get_session() as session:
        user = await user_crud.create(
            session,
            username=username,
            email=email,
            age=age
        )
        return user

# 批量导入用户
async def import_users(users_data: list[dict]):
    async with get_session() as session:
        users = await user_crud.bulk_create(session, users_data)
        return users

# 搜索用户
async def search_users(keyword: str, page: int = 1):
    builder = QueryBuilder(User)
    paginator = Paginator(User)

    async with get_session() as session:
        # 使用查询构建器构建复杂查询
        builder = (
            builder
            .filter(status="active")
            .or_(
                QueryBuilder(User).like(username=f"%{keyword}%"),
                QueryBuilder(User).like(email=f"%{keyword}%")
            )
        )

        # 获取符合条件的用户数量
        count = await builder.count(session)

        # 分页查询
        page_result = await paginator.paginate(
            session,
            page=page,
            page_size=20,
            filters={"status": "active"},
            order_by="created_at",
            desc=True
        )

        return page_result

# 获取活跃用户统计
async def get_active_users_stats():
    builder = QueryBuilder(User)

    async with get_session() as session:
        # 18-30岁活跃用户
        young_count = await (
            builder
            .filter(status="active")
            .gte(age=18)
            .lte(age=30)
            .count(session)
        )

        # 30岁以上活跃用户
        senior_count = await (
            QueryBuilder(User)
            .filter(status="active")
            .gt(age=30)
            .count(session)
        )

        return {
            "young": young_count,
            "senior": senior_count
        }
```

### 示例 2：文章管理系统（带软删除）

```python
from cathaybot.database import SoftDeleteModel, SoftDeleteCRUD, SoftDeleteQueryBuilder, get_session
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

# 定义模型
class Article(SoftDeleteModel):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="draft")

# 创建 CRUD 实例
article_crud = SoftDeleteCRUD(Article)

# 发布文章
async def publish_article(title: str, content: str, author_id: int):
    async with get_session() as session:
        article = await article_crud.create(
            session,
            title=title,
            content=content,
            author_id=author_id,
            status="published"
        )
        return article

# 删除文章（软删除）
async def delete_article(article_id: int):
    async with get_session() as session:
        success = await article_crud.soft_delete(session, id=article_id)
        return success

# 恢复文章
async def restore_article(article_id: int):
    async with get_session() as session:
        success = await article_crud.restore(session, id=article_id)
        return success

# 获取已发布文章（不包含已删除）
async def get_published_articles(page: int = 1):
    builder = SoftDeleteQueryBuilder(Article)

    async with get_session() as session:
        articles = await (
            builder
            .filter(status="published")
            .order_by("created_at", desc=True)
            .limit(20)
            .offset((page - 1) * 20)
            .all(session)
        )
        return articles

# 查看回收站（已删除的文章）
async def get_deleted_articles():
    builder = SoftDeleteQueryBuilder(Article)

    async with get_session() as session:
        articles = await (
            builder
            .only_deleted()
            .order_by("deleted_at", desc=True)
            .all(session)
        )
        return articles

# 清空回收站（永久删除）
async def empty_trash():
    async with get_session() as session:
        # 获取所有已删除的文章 ID
        builder = SoftDeleteQueryBuilder(Article)
        deleted_articles = await builder.only_deleted().all(session)

        # 永久删除
        ids = [article.id for article in deleted_articles]
        count = await article_crud.bulk_delete(session, ids)
        return count
```

---

## 最佳实践

### 1. 使用上下文管理器

始终使用 `get_session()` 上下文管理器，确保事务正确提交或回滚：

```python
async with get_session() as session:
    # 数据库操作
    user = await user_crud.create(session, username="alice")
    # 自动提交
```

### 2. 批量操作优化性能

对于大量数据操作，使用批量方法：

```python
# ❌ 不推荐：循环创建
for data in large_dataset:
    await user_crud.create(session, **data)

# ✅ 推荐：批量创建
await user_crud.bulk_create(session, large_dataset)
```

### 3. 合理使用软删除

对于需要保留历史记录的数据使用软删除：

```python
# 用户数据、订单记录等重要数据
class Order(SoftDeleteModel):
    __tablename__ = "orders"
    # ...

# 临时数据、缓存数据等可以使用硬删除
class Cache(BaseModel):
    __tablename__ = "cache"
    # ...
```

### 4. 查询构建器 vs 直接 SQL

简单查询使用 CRUD 方法，复杂查询使用查询构建器：

```python
# 简单查询
user = await user_crud.get_by(session, username="alice")

# 复杂查询
users = await (
    QueryBuilder(User)
    .filter(status="active")
    .gt(age=18)
    .like(username="%admin%")
    .order_by("created_at", desc=True)
    .limit(10)
    .all(session)
)
```

### 5. 分页查询

对于列表展示，使用分页器：

```python
paginator = Paginator(User)
page = await paginator.paginate(
    session,
    page=request.page,
    page_size=20,
    filters={"status": "active"}
)

return {
    "items": [user.to_dict() for user in page.items],
    "total": page.total,
    "page": page.page,
    "total_pages": page.total_pages
}
```

---

## 常见问题

### Q: 如何处理事务？

A: `get_session()` 会自动处理事务，成功时提交，异常时回滚：

```python
async with get_session() as session:
    try:
        user = await user_crud.create(session, username="alice")
        post = await post_crud.create(session, user_id=user.id, title="Hello")
        # 自动提交
    except Exception as e:
        # 自动回滚
        raise
```

### Q: 如何进行关联查询？

A: 使用 SQLAlchemy 的关系和 joinedload：

```python
from sqlalchemy.orm import relationship, joinedload

class User(BaseModel):
    __tablename__ = "users"
    posts = relationship("Post", back_populates="user")

class Post(BaseModel):
    __tablename__ = "posts"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="posts")

# 查询时加载关联数据
async with get_session() as session:
    result = await session.execute(
        select(User).options(joinedload(User.posts))
    )
    users = result.unique().scalars().all()
```

### Q: 软删除后如何完全清理数据？

A: 使用 `hard_delete` 方法：

```python
# 先软删除
await article_crud.soft_delete(session, id=1)

# 确认后永久删除
await article_crud.hard_delete(session, id=1)
```

---

## 总结

CathayBot 数据库模块提供了完整的数据库操作功能，涵盖了常见的使用场景。通过合理使用这些功能，可以大大简化数据库操作代码，提高开发效率。
