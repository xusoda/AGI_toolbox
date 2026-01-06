"""Profile注册表：加载profiles目录下的所有yaml文件并匹配URL"""
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
    ParseConfig,
    FieldExtractConfig,
    TransformSpec,
    GotoConfig,
    WaitForConfig,
    ViewportConfig,
    ProcessStep,
)


class ProfileRegistry:
    """Profile注册表"""

    def __init__(self, profiles_path: str):
        """
        初始化注册表
        
        Args:
            profiles_path: profiles.yaml文件路径或profiles目录路径
        """
        self.profiles_path = Path(profiles_path)
        self.profiles: List[Profile] = []
        self._load_profiles()

    def _load_profiles(self):
        """加载profiles目录下的所有yaml文件"""
        yaml_files = []
        
        if self.profiles_path.is_file():
            # 如果是文件，直接加载
            yaml_files = [self.profiles_path]
        elif self.profiles_path.is_dir():
            # 如果是目录，加载目录下所有yaml文件
            yaml_files = list(self.profiles_path.glob("*.yaml")) + list(self.profiles_path.glob("*.yml"))
        else:
            raise FileNotFoundError(f"配置文件或目录不存在: {self.profiles_path}")

        if not yaml_files:
            raise FileNotFoundError(f"未找到任何yaml配置文件: {self.profiles_path}")

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                
                if not data:
                    continue
                
                # 支持两种格式：
                # 1. 旧格式：profiles.yaml 包含 profiles 列表
                # 2. 新格式：单个文件就是一个profile
                if "profiles" in data:
                    # 旧格式：profiles.yaml
                    profiles_data = data.get("profiles", [])
                    for profile_data in profiles_data:
                        profile = self._parse_profile(profile_data)
                        self.profiles.append(profile)
                else:
                    # 新格式：单个文件就是一个profile
                    profile = self._parse_profile(data)
                    self.profiles.append(profile)
            except Exception as e:
                print(f"警告: 加载配置文件 {yaml_file} 时出错: {e}")
                continue

        # 按priority降序排序，优先级高的在前
        self.profiles.sort(key=lambda p: p.match.priority, reverse=True)

    def _parse_profile(self, data: dict) -> Profile:
        """解析单个profile配置（支持新旧两种格式）"""
        # 解析match配置
        match_data = data.get("match", {})
        match_config = MatchConfig(
            domains=match_data.get("domains"),
            url_regex=match_data.get("url_regex"),
            priority=match_data.get("priority", 0),
        )

        # 解析fetch配置（支持新格式）
        fetch_data = data.get("fetch", {})
        
        # 解析goto配置
        goto_config = None
        if "goto" in fetch_data:
            goto_data = fetch_data["goto"]
            goto_config = GotoConfig(
                wait_until=goto_data.get("wait_until", "load"),
                timeout_ms=goto_data.get("timeout_ms", 30000),
            )
        elif "wait_until" in fetch_data or "timeout_ms" in fetch_data:
            # 兼容旧格式
            goto_config = GotoConfig(
                wait_until=fetch_data.get("wait_until", "load"),
                timeout_ms=fetch_data.get("timeout_ms", 30000),
            )
        
        # 解析wait_for配置
        wait_for_configs = None
        if "wait_for" in fetch_data:
            wait_for_configs = []
            for wait_data in fetch_data["wait_for"]:
                wait_for_configs.append(
                    WaitForConfig(
                        selector=wait_data["selector"],
                        state=wait_data.get("state", "attached"),
                    )
                )
        
        # 解析viewport配置
        viewport_config = None
        if "viewport" in fetch_data:
            viewport_data = fetch_data["viewport"]
            viewport_config = ViewportConfig(
                width=viewport_data.get("width", 1280),
                height=viewport_data.get("height", 720),
            )
        
        fetch_config = FetchConfig(
            engine=fetch_data.get("engine", "playwright"),
            wait_until=goto_config.wait_until if goto_config else fetch_data.get("wait_until", "load"),
            timeout_ms=goto_config.timeout_ms if goto_config else fetch_data.get("timeout_ms", 30000),
            user_agent=fetch_data.get("user_agent"),
            goto=goto_config,
            wait_for=wait_for_configs,
            viewport=viewport_config,
        )

        # 解析parse配置（新格式）
        parse_config = None
        if "parse" in data:
            parse_data = data.get("parse", {})
            fields_config = {}
            
            for field_name, field_data in parse_data.get("fields", {}).items():
                # 解析transforms
                transforms = []
                for transform_data in field_data.get("transforms", []):
                    # 兼容两种格式：
                    # 1. {type: "url_join", config: {base: "..."}}
                    # 2. {type: "url_join", base: "..."}
                    transform_type = transform_data["type"]
                    if "config" in transform_data:
                        transform_config = transform_data["config"]
                    else:
                        # 直接写参数的情况，排除 type 字段
                        transform_config = {k: v for k, v in transform_data.items() if k != "type"}
                    
                    transforms.append(
                        TransformSpec(
                            type=transform_type,
                            config=transform_config
                        )
                    )
                
                fields_config[field_name] = FieldExtractConfig(
                    selector=field_data.get("selector"),
                    attr=field_data.get("attr"),
                    attr_candidates=field_data.get("attr_candidates"),
                    text=field_data.get("text", False),
                    transforms=transforms,
                )
            
            # 解析预处理和后处理步骤
            pre_list_process = None
            if "pre_list_process" in parse_data:
                pre_list_process = []
                for step_data in parse_data["pre_list_process"]:
                    # 兼容两种格式：
                    # 1. {method: "deduplicate_by_url", config: {url_field: "product_url"}}
                    # 2. {method: "deduplicate_by_url", url_field: "product_url"}
                    method = step_data["method"]
                    if "config" in step_data:
                        step_config = step_data["config"]
                    else:
                        # 直接写参数的情况，排除 method 字段
                        step_config = {k: v for k, v in step_data.items() if k != "method"}
                    pre_list_process.append(ProcessStep(method=method, config=step_config))
            
            post_list_process = None
            if "post_list_process" in parse_data:
                post_list_process = []
                for step_data in parse_data["post_list_process"]:
                    # 兼容两种格式：
                    # 1. {method: "deduplicate_by_url", config: {url_field: "product_url"}}
                    # 2. {method: "deduplicate_by_url", url_field: "product_url"}
                    method = step_data["method"]
                    if "config" in step_data:
                        step_config = step_data["config"]
                    else:
                        # 直接写参数的情况，排除 method 字段
                        step_config = {k: v for k, v in step_data.items() if k != "method"}
                    post_list_process.append(ProcessStep(method=method, config=step_config))
            
            parse_config = ParseConfig(
                type=parse_data.get("type", "single"),
                item_selector_candidates=parse_data.get("item_selector_candidates"),
                item_selector_pick=parse_data.get("item_selector_pick", "first_non_empty"),
                fields=fields_config,
                pre_list_process=pre_list_process,
                post_list_process=post_list_process,
            )

        # 解析fields配置（旧格式，兼容）
        fields: Optional[dict] = None
        if "fields" in data and not parse_config:
            fields = {}
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

        # 获取name（支持id或name字段）
        name = data.get("name") or data.get("id") or "unnamed_profile"

        return Profile(
            name=name,
            match=match_config,
            fetch=fetch_config,
            fields=fields,
            parse=parse_config,
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

