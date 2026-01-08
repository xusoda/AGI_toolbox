"""字典加载器：从 YAML 文件加载字典数据"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache
# 延迟导入 Normalizer 以避免循环导入
# from .normalizer import Normalizer


class DictionaryLoader:
    """字典加载器，负责加载和管理字典数据"""
    
    _cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def load_watch_dict(cls, dict_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载腕表字典
        
        Args:
            dict_path: 字典文件路径，如果为None则使用默认路径
            
        Returns:
            字典数据
        """
        if dict_path is None:
            # 默认路径：i18n/dictionaries/watch.yaml
            base_path = Path(__file__).parent.parent.parent
            dict_path = str(base_path / "i18n" / "dictionaries" / "watch.yaml")
        
        # 使用缓存
        if dict_path in cls._cache:
            return cls._cache[dict_path]
        
        try:
            with open(dict_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                cls._cache[dict_path] = data
                return data
        except Exception as e:
            print(f"[DictionaryLoader] 加载字典失败: {e}")
            return {}
    
    @classmethod
    def get_brand_aliases(cls, category: str = "watch") -> Dict[str, List[str]]:
        """
        获取所有品牌的别名映射
        
        Args:
            category: 商品类别
            
        Returns:
            {标准品牌名: [别名列表]}
        """
        if category == "watch":
            watch_dict = cls.load_watch_dict()
            result = {}
            for brand_name, brand_data in watch_dict.items():
                if isinstance(brand_data, dict):
                    aliases = brand_data.get("aliases", [])
                    result[brand_name] = aliases
            return result
        return {}
    
    @classmethod
    def get_model_aliases(
        cls, 
        brand_name: str, 
        category: str = "watch"
    ) -> Dict[str, List[str]]:
        """
        获取指定品牌下所有型号的别名映射
        
        Args:
            brand_name: 品牌名
            category: 商品类别
            
        Returns:
            {标准型号名: [别名列表]}
        """
        if category == "watch":
            watch_dict = cls.load_watch_dict()
            brand_data = watch_dict.get(brand_name, {})
            if not isinstance(brand_data, dict):
                return {}
            
            model_dict = brand_data.get("model_name", {})
            if not isinstance(model_dict, dict):
                return {}
            
            result = {}
            for model_name, model_info in model_dict.items():
                if isinstance(model_info, dict):
                    aliases = model_info.get("aliases", [])
                    result[model_name] = aliases
            return result
        return {}
    
    @classmethod
    def find_brand_by_alias(cls, alias: str, category: str = "watch") -> Optional[str]:
        """
        通过别名查找标准品牌名
        
        Args:
            alias: 品牌别名
            category: 商品类别
            
        Returns:
            标准品牌名，如果未找到则返回None
        """
        aliases_map = cls.get_brand_aliases(category)
        
        # 精确匹配
        for brand_name, aliases in aliases_map.items():
            if alias == brand_name or alias in aliases:
                return brand_name
        
        # 模糊匹配（忽略大小写和空格）
        alias_normalized = alias.lower().strip()
        for brand_name, aliases in aliases_map.items():
            if brand_name.lower().strip() == alias_normalized:
                return brand_name
            for a in aliases:
                if a.lower().strip() == alias_normalized:
                    return brand_name
        
        # 使用规范化匹配（忽略标点符号）
        # 延迟导入以避免循环导入
        from .normalizer import Normalizer
        alias_for_matching = Normalizer.normalize_for_matching(alias).lower()
        for brand_name, aliases in aliases_map.items():
            brand_for_matching = Normalizer.normalize_for_matching(brand_name).lower()
            if brand_for_matching == alias_for_matching:
                return brand_name
            for a in aliases:
                alias_for_matching_candidate = Normalizer.normalize_for_matching(a).lower()
                if alias_for_matching_candidate == alias_for_matching:
                    return brand_name
        
        return None
    
    @classmethod
    def find_model_by_alias(
        cls,
        brand_name: str,
        alias: str,
        category: str = "watch"
    ) -> Optional[str]:
        """
        通过别名查找标准型号名
        
        Args:
            brand_name: 品牌名
            alias: 型号别名
            category: 商品类别
            
        Returns:
            标准型号名，如果未找到则返回None
        """
        aliases_map = cls.get_model_aliases(brand_name, category)
        
        # 精确匹配
        for model_name, aliases in aliases_map.items():
            if alias == model_name or alias in aliases:
                return model_name
        
        # 模糊匹配（忽略大小写和空格）
        alias_normalized = alias.lower().strip()
        for model_name, aliases in aliases_map.items():
            if model_name.lower().strip() == alias_normalized:
                return model_name
            for a in aliases:
                if a.lower().strip() == alias_normalized:
                    return model_name
        
        # 使用规范化匹配（忽略标点符号）
        # 延迟导入以避免循环导入
        from .normalizer import Normalizer
        alias_for_matching = Normalizer.normalize_for_matching(alias).lower()
        for model_name, aliases in aliases_map.items():
            model_for_matching = Normalizer.normalize_for_matching(model_name).lower()
            if model_for_matching == alias_for_matching:
                return model_name
            for a in aliases:
                alias_for_matching_candidate = Normalizer.normalize_for_matching(a).lower()
                if alias_for_matching_candidate == alias_for_matching:
                    return model_name
        
        return None

