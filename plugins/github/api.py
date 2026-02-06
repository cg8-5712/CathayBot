"""
GitHub API 调用封装
"""

from typing import Optional
from dataclasses import dataclass

import httpx
from nonebot import logger


@dataclass
class GitHubUser:
    """GitHub 用户信息"""
    login: str
    name: Optional[str]
    avatar_url: str
    bio: Optional[str]
    public_repos: int
    followers: int
    following: int
    # 额外统计 (需要额外请求)
    total_stars: int = 0
    total_forks: int = 0
    total_commits: int = 0
    total_prs: int = 0
    top_languages: list[str] = None
    top_repos: list[dict] = None

    def __post_init__(self):
        if self.top_languages is None:
            self.top_languages = []
        if self.top_repos is None:
            self.top_repos = []


@dataclass
class GitHubRepo:
    """GitHub 仓库信息"""
    name: str
    full_name: str
    owner_login: str
    owner_avatar: str
    description: Optional[str]
    language: Optional[str]
    stargazers_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    topics: list[str]
    license_name: Optional[str]
    created_at: str
    updated_at: str
    homepage: Optional[str]


class GitHubAPI:
    """GitHub API 客户端"""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str = ""):
        self.token = token
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CathayBot-GitHub-Plugin",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=self.headers,
                timeout=10.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_user(self, username: str) -> Optional[GitHubUser]:
        """获取用户信息"""
        try:
            client = await self._get_client()
            resp = await client.get(f"/users/{username}")

            if resp.status_code != 200:
                return None

            data = resp.json()

            user = GitHubUser(
                login=data["login"],
                name=data.get("name"),
                avatar_url=data["avatar_url"],
                bio=data.get("bio"),
                public_repos=data["public_repos"],
                followers=data["followers"],
                following=data["following"],
            )

            # 获取额外统计信息
            await self._fetch_user_stats(client, user)

            return user

        except Exception as e:
            logger.error(f"获取 GitHub 用户失败: {e}")
            return None

    async def _fetch_user_stats(self, client: httpx.AsyncClient, user: GitHubUser):
        """获取用户额外统计信息"""
        try:
            # 获取用户仓库列表
            repos_resp = await client.get(
                f"/users/{user.login}/repos",
                params={"per_page": 100, "sort": "updated"}
            )

            if repos_resp.status_code == 200:
                repos = repos_resp.json()

                total_stars = 0
                total_forks = 0
                languages = {}
                top_repos = []

                for repo in repos:
                    if not repo.get("fork"):  # 排除 fork 的仓库
                        stars = repo.get("stargazers_count", 0)
                        forks = repo.get("forks_count", 0)
                        total_stars += stars
                        total_forks += forks

                        # 统计语言
                        lang = repo.get("language")
                        if lang:
                            languages[lang] = languages.get(lang, 0) + 1

                        # 收集热门仓库
                        top_repos.append({
                            "name": repo["name"],
                            "stars": stars,
                            "forks": forks,
                        })

                user.total_stars = total_stars
                user.total_forks = total_forks

                # 按使用次数排序语言
                sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
                user.top_languages = [lang for lang, _ in sorted_langs[:5]]

                # 按 star 排序仓库
                top_repos.sort(key=lambda x: x["stars"], reverse=True)
                user.top_repos = top_repos[:3]

            # 获取用户的 commits 数量（通过搜索 API）
            try:
                commits_resp = await client.get(
                    "/search/commits",
                    params={
                        "q": f"author:{user.login}",
                        "per_page": 1
                    },
                    headers={"Accept": "application/vnd.github.cloak-preview+json"}
                )
                if commits_resp.status_code == 200:
                    commits_data = commits_resp.json()
                    user.total_commits = commits_data.get("total_count", 0)
            except Exception as e:
                logger.debug(f"获取 commits 数量失败: {e}")

            # 获取用户的 PR 数量（通过搜索 API）
            try:
                prs_resp = await client.get(
                    "/search/issues",
                    params={
                        "q": f"author:{user.login} type:pr",
                        "per_page": 1
                    }
                )
                if prs_resp.status_code == 200:
                    prs_data = prs_resp.json()
                    user.total_prs = prs_data.get("total_count", 0)
            except Exception as e:
                logger.debug(f"获取 PR 数量失败: {e}")

        except Exception as e:
            logger.warning(f"获取用户统计信息失败: {e}")

    async def get_repo(self, owner: str, repo: str) -> Optional[GitHubRepo]:
        """获取仓库信息"""
        try:
            client = await self._get_client()
            resp = await client.get(f"/repos/{owner}/{repo}")

            if resp.status_code != 200:
                return None

            data = resp.json()

            return GitHubRepo(
                name=data["name"],
                full_name=data["full_name"],
                owner_login=data["owner"]["login"],
                owner_avatar=data["owner"]["avatar_url"],
                description=data.get("description"),
                language=data.get("language"),
                stargazers_count=data["stargazers_count"],
                forks_count=data["forks_count"],
                watchers_count=data["watchers_count"],
                open_issues_count=data["open_issues_count"],
                topics=data.get("topics", []),
                license_name=data["license"]["name"] if data.get("license") else None,
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                homepage=data.get("homepage"),
            )

        except Exception as e:
            logger.error(f"获取 GitHub 仓库失败: {e}")
            return None


# 全局 API 实例
github_api = GitHubAPI()
