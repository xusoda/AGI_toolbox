"""别名解析器：基于词表解析品牌/型号别名"""
import logging
from typing import List, Dict, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
possible_roots = [
    Path(__file__).parent.parent.parent,  # 从 search/i18n/alias_resolver.py 向上3级到 GoodsHunter
    Path("/app").parent,  # Docker 容器中
]

for root in possible_roots:
    try:
        i18n_path = root / "i18n"
        if i18n_path.exists() and i18n_path.is_dir():
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            break
    except (OSError, PermissionError):
        continue

try:
    from i18n.translation.loader import DictionaryLoader
except ImportError:
    DictionaryLoader = None
    logging.warning("DictionaryLoader 不可用，别名解析功能受限")

logger = logging.getLogger(__name__)


class AliasResolver:
    """别名解析器，负责从词表中获取同义词"""
    
    @staticmethod
    def get_brand_aliases(brand_name: str, category: str = "watch") -> List[str]:
        """
        获取品牌的别名列表（包含原始名称和所有同义词）
        
        Args:
            brand_name: 标准品牌名
            category: 商品类别
            
        Returns:
            别名列表，包含原始名称和所有同义词
        """
        if not brand_name:
            return []
        
        if DictionaryLoader is None:
            # 如果 DictionaryLoader 不可用，只返回原始名称
            return [brand_name]
        
        try:
            aliases_map = DictionaryLoader.get_brand_aliases(category)
            aliases = aliases_map.get(brand_name, [])
            
            # 返回原始名称 + 所有别名（去重，不区分大小写）
            result = [brand_name] + aliases
            
            # 去重（忽略大小写）
            seen = set()
            unique_result = []
            for alias in result:
                alias_lower = alias.lower().strip()
                if alias_lower and alias_lower not in seen:
                    seen.add(alias_lower)
                    unique_result.append(alias.strip())
            
            return unique_result if unique_result else [brand_name]
        except Exception as e:
            logger.warning(f"获取品牌别名失败 (brand_name={brand_name}): {e}", exc_info=True)
            return [brand_name]
    
    @staticmethod
    def get_model_aliases(
        brand_name: str, 
        model_name: str, 
        category: str = "watch"
    ) -> List[str]:
        """
        获取型号的别名列表
        
        Args:
            brand_name: 标准品牌名
            model_name: 标准型号名
            category: 商品类别
            
        Returns:
            别名列表
        """
        if not model_name:
            return []
        
        if DictionaryLoader is None:
            return [model_name]
        
        try:
            aliases_map = DictionaryLoader.get_model_aliases(brand_name, category)
            aliases = aliases_map.get(model_name, [])
            
            result = [model_name] + aliases
            
            # 去重
            seen = set()
            unique_result = []
            for alias in result:
                alias_lower = alias.lower().strip()
                if alias_lower and alias_lower not in seen:
                    seen.add(alias_lower)
                    unique_result.append(alias.strip())
            
            return unique_result if unique_result else [model_name]
        except Exception as e:
            logger.warning(f"获取型号别名失败 (brand_name={brand_name}, model_name={model_name}): {e}", exc_info=True)
            return [model_name]
