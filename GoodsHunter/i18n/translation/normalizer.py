"""归一化处理器：将多语言文本归一化为标准英文格式"""
import re
from typing import Optional, Tuple
from .loader import DictionaryLoader


class Normalizer:
    """归一化处理器，负责将多语言文本转换为标准英文格式"""
    
    @staticmethod
    def normalize_brand(brand_name: str, category: str = "watch") -> str:
        """
        将品牌名归一化为标准英文格式
        
        Args:
            brand_name: 原始品牌名（可能是日文、中文、英文等）
            category: 商品类别
            
        Returns:
            标准化的英文品牌名
        """
        if not brand_name:
            return ""
        
        # 去除首尾空格
        brand_name = brand_name.strip()
        
        # 尝试通过字典查找标准品牌名
        standard_brand = DictionaryLoader.find_brand_by_alias(brand_name, category)
        if standard_brand:
            return standard_brand
        
        # 如果找不到，返回原始值（可能是新的品牌，需要后续处理）
        return brand_name
    
    @staticmethod
    def normalize_model_name(
        brand_name: str,
        model_name: str,
        category: str = "watch"
    ) -> str:
        """
        将型号名归一化为标准英文格式
        
        Args:
            brand_name: 品牌名（已归一化）
            model_name: 原始型号名（可能是日文、中文、英文等）
            category: 商品类别
            
        Returns:
            标准化的英文型号名
        """
        if not model_name:
            return ""
        
        # 去除首尾空格
        model_name = model_name.strip()
        
        # 先归一化品牌名
        normalized_brand = Normalizer.normalize_brand(brand_name, category)
        
        # 尝试通过字典查找标准型号名
        standard_model = DictionaryLoader.find_model_by_alias(
            normalized_brand,
            model_name,
            category
        )
        if standard_model:
            return standard_model
        
        # 如果找不到，返回原始值
        return model_name
    
    @staticmethod
    def normalize_model_no(model_no: str) -> str:
        """
        将型号编号标准化（去除空格、统一格式等）
        
        Args:
            model_no: 原始型号编号
            
        Returns:
            标准化后的型号编号
        """
        if not model_no:
            return ""
        
        # 去除首尾空格
        model_no = model_no.strip()
        
        # 去除中间空格
        model_no = re.sub(r'\s+', '', model_no)
        
        # 统一大小写（通常型号编号是大写）
        model_no = model_no.upper()
        
        return model_no
    
    @staticmethod
    def normalize_item(
        brand_name: Optional[str],
        model_name: Optional[str],
        model_no: Optional[str],
        category: str = "watch"
    ) -> Tuple[str, str, str]:
        """
        归一化整个商品信息
        
        Args:
            brand_name: 原始品牌名
            model_name: 原始型号名
            model_no: 原始型号编号
            category: 商品类别
            
        Returns:
            (归一化后的品牌名, 归一化后的型号名, 归一化后的型号编号)
        """
        normalized_brand = Normalizer.normalize_brand(
            brand_name or "", 
            category
        )
        normalized_model = Normalizer.normalize_model_name(
            normalized_brand,
            model_name or "",
            category
        )
        normalized_model_no = Normalizer.normalize_model_no(model_no or "")
        
        return (normalized_brand, normalized_model, normalized_model_no)

