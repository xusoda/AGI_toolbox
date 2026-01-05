"""Profile注册表：加载profiles.yaml并匹配URL"""
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import yaml

from core.types import (
    Profile,
    MatchConfig,
    FetchConfig,
    StrategySpec,
    StrategyType,
)


class ProfileRegistry:
    """Profile注册表"""

    def __init__(self, profiles_path: str):
        """
        初始化注册表
        
        Args:
            profiles_path: profiles.yaml文件路径
        """
        self.profiles_path = Path(profiles_path)
        self.profiles: List[Profile] = []
        self._load_profiles()

    def _load_profiles(self):
        """加载profiles.yaml"""
        if not self.profiles_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.profiles_path}")

        with open(self.profiles_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        profiles_data = data.get("profiles", [])
        for profile_data in profiles_data:
            profile = self._parse_profile(profile_data)
            self.profiles.append(profile)

        # 按priority降序排序，优先级高的在前
        self.profiles.sort(key=lambda p: p.match.priority, reverse=True)

    def _parse_profile(self, data: dict) -> Profile:
        """解析单个profile配置"""
        # 解析match配置
        match_data = data.get("match", {})
        match_config = MatchConfig(
            domains=match_data.get("domains"),
            url_regex=match_data.get("url_regex"),
            priority=match_data.get("priority", 0),
        )

        # 解析fetch配置
        fetch_data = data.get("fetch", {})
        fetch_config = FetchConfig(
            wait_until=fetch_data.get("wait_until", "load"),
            timeout_ms=fetch_data.get("timeout_ms", 30000),
            user_agent=fetch_data.get("user_agent"),
        )

        # 解析fields配置
        fields: dict = {}
        fields_data = data.get("fields", {})
        for field_name, strategies_data in fields_data.items():
            strategies = []
            for strategy_data in strategies_data:
                strategy_type = StrategyType(strategy_data["type"])
                strategy_config = strategy_data.get("config", {})
                strategies.append(
                    StrategySpec(type=strategy_type, config=strategy_config)
                )
            fields[field_name] = strategies

        return Profile(
            name=data["name"],
            match=match_config,
            fetch=fetch_config,
            fields=fields,
            plugin=data.get("plugin"),
        )

    def match_profile(self, url: str) -> Optional[Profile]:
        """
        根据URL匹配Profile
        
        Args:
            url: 目标URL
            
        Returns:
            匹配到的Profile，如果没有匹配则返回None
        """
        parsed = urlparse(url)
        domain = parsed.netloc

        for profile in self.profiles:
            match_config = profile.match

            # 检查domain匹配
            if match_config.domains:
                if domain in match_config.domains:
                    return profile

            # 检查url_regex匹配
            if match_config.url_regex:
                if re.search(match_config.url_regex, url):
                    return profile

        return None

