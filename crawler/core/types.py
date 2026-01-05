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
class TransformSpec:
    """Transform规格"""
    type: str  # url_join, strip, regex_capture, replace, to_int, pick_best_srcset
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldExtractConfig:
    """字段提取配置（新格式）"""
    selector: Optional[str] = None
    attr: Optional[str] = None
    attr_candidates: Optional[List[str]] = None
    text: bool = False
    transforms: List[TransformSpec] = field(default_factory=list)


@dataclass
class ParseConfig:
    """解析配置"""
    type: str = "single"  # single 或 list
    item_selector_candidates: Optional[List[str]] = None
    item_selector_pick: str = "first_non_empty"  # first_non_empty 或 all
    fields: Dict[str, FieldExtractConfig] = field(default_factory=dict)


@dataclass
class WaitForConfig:
    """等待配置"""
    selector: str
    state: str = "attached"  # attached, visible, hidden, etc.


@dataclass
class ViewportConfig:
    """视口配置"""
    width: int = 1280
    height: int = 720


@dataclass
class GotoConfig:
    """导航配置"""
    wait_until: str = "load"
    timeout_ms: int = 30000


@dataclass
class MatchConfig:
    """URL匹配配置"""
    domains: Optional[List[str]] = None
    url_regex: Optional[str] = None
    priority: int = 0


@dataclass
class FetchConfig:
    """抓取配置"""
    engine: str = "playwright"  # playwright 或 http
    wait_until: str = "load"  # load, domcontentloaded, networkidle
    timeout_ms: int = 30000
    user_agent: Optional[str] = None
    goto: Optional[GotoConfig] = None
    wait_for: Optional[List[WaitForConfig]] = None
    viewport: Optional[ViewportConfig] = None


@dataclass
class Profile:
    """站点配置Profile"""
    name: str
    match: MatchConfig
    fetch: FetchConfig
    # 兼容旧格式和新格式
    fields: Optional[Dict[str, List[StrategySpec]]] = None  # 旧格式：字段名 -> 策略链
    parse: Optional[ParseConfig] = None  # 新格式：解析配置
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

