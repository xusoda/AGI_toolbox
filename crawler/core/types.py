"""核心类型定义"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class StrategyType(str, Enum):
    """抽取策略类型"""
    JSONLD = "jsonld"
    XPATH = "xpath"
    REGEX = "regex"


@dataclass
class StrategySpec:
    """策略规格"""
    type: StrategyType
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchConfig:
    """URL匹配配置"""
    domains: Optional[List[str]] = None
    url_regex: Optional[str] = None
    priority: int = 0


@dataclass
class FetchConfig:
    """抓取配置"""
    wait_until: str = "load"  # load, domcontentloaded, networkidle
    timeout_ms: int = 30000
    user_agent: Optional[str] = None


@dataclass
class Profile:
    """站点配置Profile"""
    name: str
    match: MatchConfig
    fetch: FetchConfig
    fields: Dict[str, List[StrategySpec]]  # 字段名 -> 策略链
    plugin: Optional[str] = None  # MVP不实现，仅预留


@dataclass
class Page:
    """抓取的页面"""
    url: str
    html: str
    status_code: int = 200


@dataclass
class FieldError:
    """字段级别的错误"""
    field: str
    error: str
    strategy: Optional[str] = None


@dataclass
class Record:
    """抽取结果记录"""
    url: str
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[FieldError] = field(default_factory=list)

