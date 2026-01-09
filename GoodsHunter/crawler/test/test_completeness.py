"""测试抓取内容完整性

验证yaml配置中定义的字段在指定比例以上的记录中都存在且满足检查标准。
支持四种检查类型：0=任意非空内容, 1=数字, 2=非空字符串, 3=URL链接
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set, Callable
from urllib.parse import urlparse

import pytest
import yaml

# 配置日志
logger = logging.getLogger(__name__)

# 将项目根目录添加到Python路径
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from core.registry import ProfileRegistry
from core.types import Profile
from fetch.playwright_fetcher import PlaywrightFetcher
from extract.engine import ExtractEngine


def load_test_config() -> Dict:
    """加载测试配置文件"""
    config_path = Path(__file__).parent / "test_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def get_profile_fields(profile: Profile) -> Set[str]:
    """从profile配置中提取所有定义的字段名"""
    fields = set()
    
    if profile.parse and profile.parse.fields:
        # 新格式：从parse.fields中提取
        fields.update(profile.parse.fields.keys())
    elif profile.fields:
        # 旧格式：从fields中提取
        fields.update(profile.fields.keys())
    
    return fields


def is_non_empty(value) -> bool:
    """检查值是否为任意非空内容（排除None、空字符串、"None"、"none"、"null"）"""
    if value is None:
        return False
    
    if isinstance(value, str):
        value = value.strip()
        # 空字符串视为无效
        if not value:
            return False
        # "None"、"none"、"null"（不区分大小写）视为无效
        if value.lower() in ("none", "null"):
            return False
        return True
    
    # 其他类型（数字、列表、字典等）视为有效
    return True


def is_number(value) -> bool:
    """检查值是否为数字"""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        # 尝试转换为数字
        try:
            float(value.replace(",", "").strip())
            return True
        except (ValueError, AttributeError):
            return False
    return False


def is_non_empty_string(value) -> bool:
    """检查值是否为非空字符串"""
    if value is None:
        return False
    if isinstance(value, str):
        # 空字符串或只包含空白字符视为无效
        return value.strip() != ""
    return False


def is_url(value) -> bool:
    """检查值是否为有效的URL链接"""
    if value is None:
        return False
    if not isinstance(value, str):
        return False
    
    value = value.strip()
    if not value:
        return False
    
    try:
        result = urlparse(value)
        # 至少需要有scheme和netloc，或者至少是相对路径（以/开头）
        return bool(result.scheme and result.netloc) or value.startswith("/")
    except Exception:
        return False


# 验证函数映射
VALIDATORS: Dict[int, Callable] = {
    0: is_non_empty,  # 任意非空内容
    1: is_number,  # 数字
    2: is_non_empty_string,  # 非空字符串
    3: is_url,  # URL链接
}


def get_field_validator(validation_type: int) -> Callable:
    """获取指定类型的验证函数"""
    return VALIDATORS.get(validation_type, is_non_empty)


def calculate_completeness(
    items: List[Dict],
    fields: Set[str],
    field_configs: Dict[str, Dict],
    default_type: int,
    default_threshold: float,
) -> Dict[str, Dict]:
    """计算每个字段的完整性（有效值占比）
    
    Returns:
        Dict[field_name, {
            'completeness': float,  # 完整性比例
            'threshold': float,      # 要求的阈值
            'type': int,             # 验证类型
        }]
    """
    if not items:
        return {
            field: {
                "completeness": 0.0,
                "threshold": field_configs.get(field, {}).get("threshold", default_threshold),
                "type": field_configs.get(field, {}).get("type", default_type),
            }
            for field in fields
        }
    
    total_count = len(items)
    field_completeness = {}
    
    for field in fields:
        # 获取字段配置（类型和阈值）
        field_config = field_configs.get(field, {})
        validation_type = field_config.get("type", default_type)
        threshold = field_config.get("threshold", default_threshold)
        
        # 获取验证函数
        validator = get_field_validator(validation_type)
        
        # 计算有效值数量
        valid_count = sum(1 for item in items if validator(item.get(field)))
        completeness = valid_count / total_count if total_count > 0 else 0.0
        
        field_completeness[field] = {
            "completeness": completeness,
            "threshold": threshold,
            "type": validation_type,
        }
    
    return field_completeness


async def fetch_and_extract(url: str, profile: Profile) -> Dict:
    """抓取并提取数据"""
    fetcher = PlaywrightFetcher()
    engine = ExtractEngine()
    
    try:
        await fetcher.start()
        page = await fetcher.fetch(url, profile.fetch)
        record = engine.extract(page, profile)
        
        # 转换为可序列化的字典
        return {
            "url": record.url,
            "data": record.data,
            "errors": [
                {
                    "field": err.field,
                    "error": err.error,
                    "strategy": err.strategy,
                }
                for err in record.errors
            ],
        }
    finally:
        await fetcher.stop()


def get_validation_type_name(validation_type: int) -> str:
    """获取验证类型的名称"""
    type_names = {
        0: "任意非空内容",
        1: "数字",
        2: "非空字符串",
        3: "URL链接",
    }
    return type_names.get(validation_type, f"未知类型({validation_type})")


@pytest.mark.asyncio
async def test_field_completeness():
    """测试字段完整性：根据配置验证字段是否满足检查标准"""
    # 加载测试配置
    test_data = load_test_config()
    
    # 获取默认配置
    defaults = test_data.get("defaults", {})
    default_type = defaults.get("type", 0)  # 默认：任意非空内容
    default_threshold = defaults.get("threshold", 0.9)  # 默认：90%
    
    profiles_config = test_data.get("profiles", {})
    
    # 加载profiles
    profiles_path = _project_root / "profiles"
    logger.info(f"加载profiles目录: {profiles_path}")
    registry = ProfileRegistry(str(profiles_path))
    logger.info(f"成功加载 {len(registry.profiles)} 个profiles: {[p.name for p in registry.profiles]}")
    
    # 为每个profile运行测试
    for profile_id, config in profiles_config.items():
        logger.info(f"开始测试 profile: {profile_id}")
        urls = config.get("urls", [])
        if not urls:
            logger.warning(f"Profile {profile_id} 没有配置测试URL，跳过")
            pytest.skip(f"Profile {profile_id} 没有配置测试URL")
        
        # 获取字段级别的配置
        field_configs = config.get("fields", {})
        
        # 找到对应的profile
        profile = None
        for p in registry.profiles:
            if p.name == profile_id:
                profile = p
                break
        
        if not profile:
            logger.error(f"未找到profile: {profile_id}，可用的profiles: {[p.name for p in registry.profiles]}")
            pytest.skip(f"未找到profile: {profile_id}")
        
        logger.info(f"找到profile: {profile_id}, 字段数: {len(get_profile_fields(profile))}")
        
        # 获取配置的字段
        expected_fields = get_profile_fields(profile)
        if not expected_fields:
            pytest.skip(f"Profile {profile_id} 没有定义字段")
        
        # 对每个测试URL执行抓取
        for url in urls:
            logger.info(f"\n{'='*60}")
            logger.info(f"测试 Profile: {profile_id}, URL: {url}")
            logger.info(f"{'='*60}")
            
            # 抓取数据
            logger.info("开始抓取数据...")
            result = await fetch_and_extract(url, profile)
            logger.info("抓取完成")
            
            # 获取items列表
            items = result.get("data", {}).get("items", [])
            if not items:
                logger.error(f"Profile {profile_id} 在URL {url} 上没有提取到任何items")
                pytest.fail(f"Profile {profile_id} 在URL {url} 上没有提取到任何items")
            
            logger.info(f"提取了 {len(items)} 个items")
            
            # 计算字段完整性
            logger.info("开始计算字段完整性...")
            completeness_results = calculate_completeness(
                items, expected_fields, field_configs, default_type, default_threshold
            )
            
            # 验证每个字段的完整性
            failed_fields = []
            
            for field, result_info in completeness_results.items():
                completeness_rate = result_info["completeness"]
                threshold = result_info["threshold"]
                validation_type = result_info["type"]
                type_name = get_validation_type_name(validation_type)
                
                logger.info(
                    f"  字段 {field}: {completeness_rate:.2%} ({completeness_rate * len(items):.0f}/{len(items)}) "
                    f"[类型: {type_name}, 要求: {threshold:.2%}]"
                )
                
                if completeness_rate < threshold:
                    failed_fields.append({
                        "field": field,
                        "completeness": completeness_rate,
                        "threshold": threshold,
                        "type": validation_type,
                        "type_name": type_name,
                    })
            
            # 如果有字段不满足要求，输出详细信息
            if failed_fields:
                error_msg = f"Profile {profile_id} 在URL {url} 上有字段不满足检查标准:\n"
                for failed in failed_fields:
                    error_msg += (
                        f"  - {failed['field']}: {failed['completeness']:.2%} "
                        f"(要求: {failed['threshold']:.2%}, 类型: {failed['type_name']})\n"
                    )
                
                # 输出一些示例数据以便调试
                error_msg += "\n前3个items的字段示例:\n"
                for i, item in enumerate(items[:3], 1):
                    error_msg += f"  Item {i}:\n"
                    for field in expected_fields:
                        value = item.get(field)
                        field_config = field_configs.get(field, {})
                        validation_type = field_config.get("type", default_type)
                        validator = get_field_validator(validation_type)
                        is_valid = validator(value)
                        type_name = get_validation_type_name(validation_type)
                        error_msg += f"    {field}: {repr(value)} (类型: {type_name}, 有效: {is_valid})\n"
                
                logger.error(error_msg)
                pytest.fail(error_msg)
            
            logger.info(f"✓ 所有字段完整性检查通过")


if __name__ == "__main__":
    # 可以直接运行测试
    pytest.main([__file__, "-v"])

